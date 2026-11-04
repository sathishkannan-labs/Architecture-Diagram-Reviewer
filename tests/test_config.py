from archreview.config import load_local_env

def test_local_settings_are_allowlisted_and_do_not_execute(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY','')
    monkeypatch.setenv('META_MODEL','terminal-choice')
    monkeypatch.delenv('AWS_SECRET_ACCESS_KEY',raising=False)
    file=tmp_path/'.env'
    file.write_text('# comment\nMODEL_API_KEY="test=key"\nMETA_MODEL=file-choice\nAWS_SECRET_ACCESS_KEY=not-allowed\nPATH=not-allowed\n')
    load_local_env(file)
    import os
    assert os.environ['MODEL_API_KEY']=='test=key'
    assert os.environ['META_MODEL']=='terminal-choice'
    assert 'AWS_SECRET_ACCESS_KEY' not in os.environ

def test_missing_env_file(tmp_path):
    load_local_env(tmp_path/'missing')


def test_non_utf8_env_is_ignored_without_losing_existing_settings(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY','existing-test-only')
    file=tmp_path/'.env';file.write_bytes('MODEL_API_KEY=other'.encode('utf-16'))
    load_local_env(file)
    import os
    assert os.environ['MODEL_API_KEY']=='existing-test-only'


def test_unreadable_env_is_ignored(tmp_path,monkeypatch):
    from pathlib import Path
    file=tmp_path/'.env';file.write_text('MODEL_API_KEY=test-only')
    def denied(*args,**kwargs):raise PermissionError('test failure')
    monkeypatch.setattr(Path,'read_text',denied)
    load_local_env(file)
