from archreview.config import load_local_env

def test_local_settings_are_allowlisted_and_do_not_execute(tmp_path,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False)
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
