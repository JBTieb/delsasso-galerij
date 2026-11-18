"""Builds "Delsasso Galerij (los bestand).html".

That file is the whole gallery in one piece: every photo from the folder "afbeeldingen" is embedded in the page
itself, and so are the 3D library and the fonts (folder "vendor"). It can be copied to any computer and
opened with a double click - no web server and no internet needed.

Angela's own titles and stories: in the gallery she presses Esc -> "Titels en verhalen aanpassen", types, and
presses "Bewaar de lijst als bestand". Save that file as titels.json next to index.html; this script then puts
her titles in the standalone file, so everyone who opens it sees them.

Run this again after every change to index.html, the photos or titels.json:

    python build_standalone.py
"""
import base64
import io
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
MIME = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
MARKER = '<script type="module">'
TARGET = 'Delsasso Galerij (los bestand).html'
SHARED = 'Delsasso Galerij.html'   # name of the copy in OneDrive\Delsasso Galerij


def data_url(path, mime):
    with open(path, 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode('ascii'))


def embed_vendor(html):
    """Puts Three.js and the fonts (folder vendor) inside the page too, so the file needs no internet at all."""
    vendor = os.path.join(HERE, 'vendor')
    old_map = ('    "three": "./vendor/three/three.module.min.js",\n'
               '    "three/addons/": "./vendor/three/addons/"')
    assert html.count(old_map) == 1, 'import map in index.html changed'
    modules = {'three': 'three/three.module.min.js'}
    for addon in ('environments/RoomEnvironment.js', 'objects/Reflector.js', 'geometries/RoundedBoxGeometry.js'):
        modules['three/addons/' + addon] = 'three/addons/' + addon
    new_map = ',\n'.join('    %s: %s' % (json.dumps(k), json.dumps(data_url(os.path.join(vendor, v), 'text/javascript'))) for k, v in modules.items())
    html = html.replace(old_map, new_map)
    css = io.open(os.path.join(vendor, 'fonts', 'fonts.css'), encoding='utf-8').read()
    for name in sorted(set(re.findall(r'url\(([\w-]+\.woff2)\)', css))):
        css = css.replace('url(%s)' % name, 'url(%s)' % data_url(os.path.join(vendor, 'fonts', name), 'font/woff2'))
    link = '<link href="vendor/fonts/fonts.css" rel="stylesheet">'
    assert html.count(link) == 1, 'font link in index.html changed'
    return html.replace(link, '<style>\n' + css + '</style>')


def main():
    html = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
    assert html.count(MARKER) == 1, 'index.html should contain exactly one module script'
    images = {}
    folder = os.path.join(HERE, 'afbeeldingen')
    for name in sorted(os.listdir(folder)):
        ext = os.path.splitext(name)[1].lower()
        if ext not in MIME:
            continue
        if 'afbeeldingen/' + name not in html and name.rsplit('.', 1)[0].rstrip('0123456789-') not in html:
            continue  # a photo the gallery does not use
        with open(os.path.join(folder, name), 'rb') as f:
            images['afbeeldingen/' + name] = 'data:%s;base64,%s' % (MIME[ext], base64.b64encode(f.read()).decode('ascii'))
    titles = {}
    titles_file = os.path.join(HERE, 'titels.json')
    if os.path.exists(titles_file):
        titles = json.load(io.open(titles_file, encoding='utf-8-sig')) or {}
    script = ('<script>window.GALLERY_IMAGES = ' + json.dumps(images) + ';\n'
              'window.GALLERY_TITLES = ' + json.dumps(titles, ensure_ascii=False) + ';</script>\n')
    out = html.replace(MARKER, script + MARKER)
    out = embed_vendor(out)
    with io.open(os.path.join(HERE, TARGET), 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print('%s: %d photos and %d own titles embedded, %.1f MB' % (TARGET, len(images), len(titles), len(out.encode('utf-8')) / 1e6))
    # keep the copy in OneDrive (the one shared with Angela) up to date
    onedrive = os.environ.get('OneDrive') or os.path.join(os.path.expanduser('~'), 'OneDrive')
    if os.path.isdir(onedrive):
        folder = os.path.join(onedrive, 'Delsasso Galerij')
        os.makedirs(folder, exist_ok=True)
        shutil.copyfile(os.path.join(HERE, TARGET), os.path.join(folder, SHARED))
        print('Copied to', os.path.join(folder, SHARED))


if __name__ == '__main__':
    main()
