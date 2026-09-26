"""Check the built reader in headless Chrome using the DevTools protocol.

Requires websocket-client in .tools/python. Produces desktop/mobile screenshots.
"""
import base64
import functools
import http.server
import json
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools/python'))
import websocket


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT / 'dist')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    process = socket = None
    artifacts = ROOT / '.artifacts'
    artifacts.mkdir(exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='songbook-browser-') as profile:
            try:
                process = subprocess.Popen([
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
                    '--remote-debugging-port=0', '--remote-allow-origins=http://localhost',
                    '--user-data-dir=' + profile, 'about:blank'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                port_file = Path(profile) / 'DevToolsActivePort'
                for _ in range(100):
                    if port_file.exists():
                        break
                    if process.poll() is not None:
                        raise RuntimeError('Chrome exited before starting DevTools')
                    time.sleep(.1)
                port = port_file.read_text().splitlines()[0]
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
                tab = next(tab for tab in tabs if tab['type'] == 'page' and tab['url'] == 'about:blank')
                socket = websocket.create_connection(tab['webSocketDebuggerUrl'], origin='http://localhost', timeout=20)
                sequence = 0
                runtime_errors = []

                def cdp(method, params=None):
                    nonlocal sequence
                    sequence += 1
                    socket.send(json.dumps({'id': sequence, 'method': method, 'params': params or {}}))
                    while True:
                        message = json.loads(socket.recv())
                        if message.get('method') == 'Runtime.exceptionThrown':
                            runtime_errors.append(message['params'])
                        if message.get('id') == sequence:
                            if 'error' in message:
                                raise RuntimeError(message['error'])
                            return message.get('result', {})

                def evaluate(expression):
                    result = cdp('Runtime.evaluate', {'expression': expression, 'awaitPromise': True, 'returnByValue': True})
                    if result.get('exceptionDetails'):
                        raise RuntimeError(result['exceptionDetails'])
                    return result['result'].get('value')

                def load(url):
                    navigation = cdp('Page.navigate', {'url': url})
                    for _ in range(100):
                        if evaluate('document.readyState === "complete" && !!document.querySelector(".lyric-text")'):
                            return
                        time.sleep(.05)
                    raise RuntimeError({'navigation': navigation, 'errors': runtime_errors, 'page': evaluate('({url:location.href,body:document.body?.innerText.slice(0,500),data:typeof window.SONGBOOK_DATA})')})

                cdp('Runtime.enable')
                url = f'http://127.0.0.1:{server.server_port}/'
                for width, height in [(1280, 1000), (390, 1000), (320, 850)]:
                    cdp('Emulation.setDeviceMetricsOverride', {'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': width < 600})
                    load(url + '#laca-25301-01')
                    result = evaluate('''(async () => {
                      const check = (ok, name) => { if (!ok) throw Error(name); };
                      const $ = s => document.querySelector(s);
                      const tick = () => new Promise(resolve => setTimeout(resolve, 25));
                      check(SONGBOOK_DATA.length === 31, '31 songs');
                      check($('#song-select').options.length === 31, '31 song choices');
                      let total = 0;
                      for (const song of SONGBOOK_DATA) {
                        location.hash = song.id; await tick();
                        check($('#song-title').textContent === song.title, 'song navigation');
                        const source = song.stanzas.flatMap(s => s.lines);
                        const rows = [...document.querySelectorAll('.lyric-line')];
                        check(rows.length === source.length, 'line counts');
                        check(document.querySelectorAll('.stanza').length === song.stanzas.length, 'stanzas');
                        for (let i = 0; i < source.length; i++) {
                          for (const layer of ['original', 'pronunciation', 'translation']) {
                            check(rows[i].querySelector('.'+layer).textContent === source[i][layer], 'exact text');
                          }
                        }
                        const styles = ['original', 'pronunciation', 'translation'].map(layer => getComputedStyle($('.'+layer)));
                        for (const key of ['fontSize', 'fontWeight', 'lineHeight', 'color', 'textAlign']) {
                          check(styles.every(style => style[key] === styles[0][key]), 'equal '+key);
                        }
                        check(!$('#lyrics').querySelector('button,[role=button],.selected'), 'plain lyrics');
                        check(document.documentElement.scrollWidth <= innerWidth, 'no overflow');
                        total += rows.length;
                      }
                      check(total === 1319, 'all lyric lines');
                      check($('#next-song').hidden, 'last-song navigation');
                      location.hash = SONGBOOK_DATA[0].id; await tick();
                      check($('#previous-song').hidden, 'first-song navigation');
                      $('.settings').open = true;
                      const before = parseFloat(getComputedStyle($('.original')).fontSize);
                      $('#larger').click();
                      for (const layer of ['original', 'pronunciation', 'translation']) {
                        check(parseFloat(getComputedStyle($('.'+layer)).fontSize) === before+1, 'equal resizing');
                      }
                      $('#smaller').click();
                      $('[data-layer=original]').click();
                      check(getComputedStyle($('.original')).display === 'none', 'hide layer');
                      $('[data-layer=pronunciation]').click();
                      $('[data-layer=translation]').click();
                      check($('[data-layer=translation]').checked, 'prevent empty view');
                      $('[data-layer=original]').click();
                      $('[data-layer=pronunciation]').click();
                      $('.settings').open = false;
                      const saved = JSON.parse(localStorage.getItem('han-sojeol-reader-v2'));
                      check(saved.size === before && saved.currentId === SONGBOOK_DATA[0].id, 'save preferences');
                      check(document.documentElement.scrollWidth <= innerWidth, 'settings no overflow');
                      return {songs:31, lines:total, fontSize:getComputedStyle($('.original')).fontSize, width:innerWidth};
                    })()''')
                    print('PASS browser:', json.dumps(result))
                    if width in [1280, 390]:
                        image = cdp('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
                        (artifacts / f'ui-{width}.png').write_bytes(base64.b64decode(image['data']))
                load((ROOT / 'index.html').as_uri() + '#laca-25303-11')
                assert evaluate('document.querySelector("#song-select").value') == 'laca-25303-11'
                print('PASS direct file access and song deep link')
            finally:
                if socket:
                    socket.close()
                if process:
                    process.terminate()
                    process.wait(timeout=10)
                time.sleep(.3)
    finally:
        server.shutdown()


if __name__ == '__main__':
    run()
