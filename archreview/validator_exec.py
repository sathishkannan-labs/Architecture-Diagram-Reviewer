"""Linux subprocess entry point: non-root, credential-free, IP networking denied.

Temporary workspaces are isolation, not a hostile-code sandbox. Only our trusted
Terraform templates may reach this process. libseccomp is required; fail closed.
"""
import ctypes
import ctypes.util
import errno
import os
import resource
import socket
import sys

class Comparison(ctypes.Structure):
    _fields_ = [('arg',ctypes.c_uint), ('op',ctypes.c_uint),
                ('datum_a',ctypes.c_uint64), ('datum_b',ctypes.c_uint64)]

def restrict_network():
    if os.getuid() == 0:
        raise RuntimeError('Refusing root validator process')
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise RuntimeError('Unable to set no_new_privs')
    name = ctypes.util.find_library('seccomp')
    if not name:
        raise RuntimeError('libseccomp unavailable')
    lib = ctypes.CDLL(name, use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    context = lib.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW
    if not context:
        raise RuntimeError('Unable to allocate seccomp context')
    deny = 0x00050000 | errno.EPERM
    try:
        number = lib.seccomp_syscall_resolve_name(b'socket')
        # Allow AF_UNIX only: Terraform provider RPC uses local Unix sockets.
        if number < 0 or lib.seccomp_rule_add(context, deny, number, 1, Comparison(0,1,socket.AF_UNIX,0)) != 0:
            raise RuntimeError('Unable to deny network sockets')
        for syscall in (b'socketcall',b'io_uring_setup'):
            number = lib.seccomp_syscall_resolve_name(syscall)
            if number >= 0 and lib.seccomp_rule_add(context,deny,number,0) != 0:
                raise RuntimeError('Unable to deny alternate network syscall')
        if lib.seccomp_load(context) != 0:
            raise RuntimeError('Unable to load network filter')
    finally:
        lib.seccomp_release(context)
    for family in (socket.AF_INET,socket.AF_INET6):
        try:
            sock = socket.socket(family,socket.SOCK_STREAM)
        except OSError as exc:
            if exc.errno == errno.EPERM:
                continue
            raise RuntimeError('Network filter self-check was inconclusive') from None
        sock.close()
        raise RuntimeError('Network filter self-check failed')

if __name__ == '__main__':
    try:
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        resource.setrlimit(resource.RLIMIT_CPU,(175,175))
        resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))
        restrict_network()
        os.execv(sys.argv[1],sys.argv[1:])
    except Exception:
        print('Validator security preflight unavailable; command was not executed.',file=sys.stderr)
        sys.exit(78)
