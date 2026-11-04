"""Render Free preview: native Python, one Streamlit process, no Terraform."""
import os
import sys

if __name__ == '__main__':
    os.environ['ARCHREVIEW_HOSTED'] = '1'
    port = int(os.getenv('PORT', '10000'))
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be between 1 and 65535')
    os.execv(sys.executable, [sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
        '--server.address=0.0.0.0', f'--server.port={port}', '--server.headless=true',
        '--server.maxUploadSize=5', '--server.maxMessageSize=10',
        '--server.fileWatcherType=none', '--browser.gatherUsageStats=false'])
