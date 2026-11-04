"""Developer recording helper; Playwright/Chromium are optional test dependencies.
Records real UI interaction. This is explicitly NOT live Meta acceptance.
"""
from pathlib import Path
import os
import subprocess
import sys
import time
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
output=root/'docs/evidence'
output.mkdir(exist_ok=True,parents=True)
server=subprocess.Popen([sys.executable,'-m','streamlit','run','streamlit_app.py',
    '--server.address=127.0.0.1','--server.port=8503','--server.headless=true',
    '--browser.gatherUsageStats=false'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':900},record_video_dir=str(output/'raw-video'),record_video_size={'width':1440,'height':900})
        page=context.new_page()
        for attempt in range(40):
            try:page.goto('http://127.0.0.1:8503');break
            except Exception:time.sleep(.25)
        def caption(text):
            page.evaluate('''text => {
              let e=document.getElementById('demo-caption');
              if(!e){e=document.createElement('div');e.id='demo-caption';document.body.appendChild(e);}
              e.style='position:fixed;bottom:0;left:0;right:0;z-index:999999;background:#142442;color:white;padding:15px 24px;font:18px sans-serif;border-top:3px solid #f5ba45';
              e.textContent='FIXTURE DEMO · '+text;
            }''',text)
        caption('Synthetic diagram; no live Meta call. Docker validation is not yet verified.')
        page.wait_for_timeout(3500)
        page.get_by_role('button',name='Load fixture (no AI call)',exact=True).click()
        page.get_by_role('button',name='Run the six-rule review',exact=True).wait_for()
        page.get_by_text('1 · Correct the extracted observations',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(output/'ui-loaded.png'),full_page=True)
        caption('1 / 6 · Inspect the editable observations and retained original extraction.')
        page.wait_for_timeout(3500)
        page.get_by_text('Quick label correction',exact=True).click()
        page.get_by_label('Corrected component label',exact=True).fill('Internet (human confirmed)')
        page.get_by_label('Correction evidence',exact=True).fill('Human confirmed the Internet label in the supplied diagram.')
        caption('2 / 6 · Record a human correction. Provenance and revision update; downstream results clear.')
        page.wait_for_timeout(2500)
        page.get_by_role('button',name='Record label correction',exact=True).click()
        page.get_by_text('1 human correction revision(s) recorded.',exact=True).wait_for()
        page.get_by_role('button',name='Run the six-rule review',exact=True).click()
        page.get_by_text('2 · Review risk evidence',exact=True).scroll_into_view_if_needed()
        caption('3 / 6 · Six mandatory checks distinguish explicit weaknesses from missing diagram information.')
        page.wait_for_timeout(4500)
        page.get_by_text('3 · Approve the proposed AWS target',exact=True).scroll_into_view_if_needed()
        caption('4 / 6 · Proposed target stays separate from observations. Decisions cite evidence and assumptions.')
        page.wait_for_timeout(4500)
        page.get_by_text('I approve this target revision and its explicit baseline assumptions.',exact=True).click()
        page.get_by_role('button',name='Record explicit approval',exact=True).click()
        page.get_by_role('button',name='Generate trusted Terraform and run actual validation',exact=True).wait_for()
        page.get_by_role('button',name='Generate trusted Terraform and run actual validation',exact=True).click()
        page.get_by_text('4 · Generate and validate',exact=True).scroll_into_view_if_needed()
        page.get_by_text('Validation status:',exact=False).wait_for()
        caption('5 / 6 · Honest result: NOT RUN. This host cannot run the required non-root validator.')
        page.wait_for_timeout(4500)
        page.get_by_role('button',name='Download artifacts · not_run',exact=True).scroll_into_view_if_needed()
        caption('6 / 6 · Every resource maps to an approved decision. Download stays available with its status.')
        page.wait_for_timeout(3500)
        with page.expect_download() as download_info:
            page.get_by_role('button',name='Download artifacts · not_run',exact=True).click()
        download_info.value.save_as(str(output/'fixture-artifacts.zip'))
        page.screenshot(path=str(output/'ui-download.png'),full_page=True)
        video=page.video
        context.close();video_path=Path(video.path());browser.close()
        subprocess.run(['ffmpeg','-y','-i',str(video_path),'-c:v','libx264','-preset','fast','-crf','25','-pix_fmt','yuv420p','-movflags','+faststart',str(output/'fixture-walkthrough.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print('Real fixture UI walkthrough recorded; downloaded ZIP verified by browser.')
finally:
    server.terminate();server.wait(timeout=10)
