#!/usr/bin/python3
"""Install/revert a local theme and the official matching User Themes extension."""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from gi.repository import Gio
from state import (data_home, snapshot_dir, settings, save_key, restore_key,
                   restore_membership, backup_tree, restore_tree, write_json)

UUID = 'user-theme@gnome-shell-extensions.gcampax.github.com'
SCHEMA = 'org.gnome.shell.extensions.user-theme'
HERE = Path(__file__).resolve().parent
DATA = data_home()
THEME = DATA / 'themes/Marbell-Ember/gnome-shell'
EXTENSION = DATA / 'gnome-shell/extensions' / UUID
SHELL = settings('org.gnome.shell')


def install():
    major = subprocess.check_output(['/usr/bin/gnome-shell', '--version'], text=True).split()[-1].split('.')[0]
    snap = snapshot_dir('shell')
    state_file = snap / 'state.json'
    if state_file.exists():
        saved = json.loads(state_file.read_text())
        if saved.get('reverted'): raise SystemExit('Snapshot already reverted; use a fresh MARBELL_EMBER_BACKUP_DIR')
    else:
        saved = {'enabled': save_key(SHELL, 'enabled-extensions'),
                 'disabled': save_key(SHELL, 'disabled-extensions'),
                 'theme_existed': backup_tree(THEME, snap/'previous-theme'),
                 'extension_existed': backup_tree(EXTENSION, snap/'previous-extension')}
        # Save even an explicit name left from an uninstalled extension via its fixed dconf path.
        saved['name_dconf'] = subprocess.check_output(['/usr/bin/dconf','read','/org/gnome/shell/extensions/user-theme/name'],text=True).strip() or None
        write_json(state_file, saved)
    with tempfile.TemporaryDirectory(prefix='marbell-shell-') as tmp:
        staging = Path(tmp)/'gnome-shell'
        subprocess.run([sys.executable, str(HERE/'build.py'), '--output', str(staging)], check=True)
        subprocess.run([str(HERE/'validate.sh'), str(staging/'gnome-shell.css')], check=True)
        if not EXTENSION.exists():
            url = 'https://extensions.gnome.org/extension-info/?' + urllib.parse.urlencode({'uuid':UUID,'shell_version':major})
            with urllib.request.urlopen(url, timeout=45) as response: info = json.load(response)
            download = urllib.parse.urljoin('https://extensions.gnome.org', info['download_url'])
            if urllib.parse.urlparse(download).hostname != 'extensions.gnome.org': raise RuntimeError('Unexpected extension download host')
            with urllib.request.urlopen(download, timeout=45) as response: archive = response.read()
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                metadata = json.loads(bundle.read('metadata.json'))
                if metadata['uuid'] != UUID or major not in metadata['shell-version']:
                    raise RuntimeError('Official extension does not match this Shell')
                for entry in bundle.infolist():
                    p = Path(entry.filename)
                    if p.is_absolute() or '..' in p.parts or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise RuntimeError('Unsafe extension archive path')
                EXTENSION.parent.mkdir(parents=True,exist_ok=True)
                bundle.extractall(EXTENSION)
            saved['download_url'] = download
            saved['archive_sha256'] = hashlib.sha256(archive).hexdigest()
            saved['extension_version'] = metadata.get('version-name', metadata['version'])
            write_json(state_file, saved)
        metadata = json.loads((EXTENSION/'metadata.json').read_text())
        if metadata['uuid'] != UUID or major not in metadata['shell-version']:
            raise RuntimeError('Existing User Themes extension is incompatible; left untouched')
        subprocess.run(['/usr/bin/glib-compile-schemas',str(EXTENSION/'schemas')],check=True)
        # Retain existing assets in the snapshot; install fully parsed output only.
        THEME.parent.mkdir(parents=True,exist_ok=True)
        if THEME.exists(): shutil.rmtree(THEME)
        shutil.copytree(staging,THEME)
    # A global user-extension mute also mutes User Themes. Preserve that baseline,
    # suppress only the installed user extensions it was keeping inactive, then unmute.
    if 'disable_user_extensions' not in saved:
        saved['disable_user_extensions'] = save_key(SHELL, 'disable-user-extensions')
        saved['suppressed_user_extensions'] = []
        if SHELL.get_boolean('disable-user-extensions'):
            enabled_now = SHELL.get_strv('enabled-extensions')
            disabled_now = SHELL.get_strv('disabled-extensions')
            for directory in EXTENSION.parent.iterdir():
                metadata_file = directory/'metadata.json'
                if directory == EXTENSION or not metadata_file.is_file(): continue
                uid = json.loads(metadata_file.read_text()).get('uuid')
                if uid in enabled_now and uid not in disabled_now:
                    saved['suppressed_user_extensions'].append(uid)
        write_json(state_file, saved)
    disabled_now = SHELL.get_strv('disabled-extensions')
    for uid in saved['suppressed_user_extensions']:
        if uid not in disabled_now: disabled_now.append(uid)
    SHELL.set_strv('disabled-extensions', disabled_now)
    Gio.Settings.sync()
    user_theme = settings(SCHEMA, EXTENSION/'schemas')
    user_theme.set_string('name','Marbell-Ember')
    enabled = SHELL.get_strv('enabled-extensions')
    if UUID not in enabled: SHELL.set_strv('enabled-extensions', enabled+[UUID])
    disabled = SHELL.get_strv('disabled-extensions')
    if UUID in disabled: SHELL.set_strv('disabled-extensions',[x for x in disabled if x != UUID])
    SHELL.set_boolean('disable-user-extensions', False)
    Gio.Settings.sync()
    print(f'Installed {THEME}; User Themes {metadata.get("version-name", metadata["version"])} enabled for next login. Snapshot: {snap}')
    if saved['suppressed_user_extensions']:
        print('Kept previously suppressed extensions disabled: ' + ', '.join(saved['suppressed_user_extensions']))


def revert():
    snap = snapshot_dir('shell',False)
    file = snap/'state.json'
    if not file.exists():
        print(f'No Shell snapshot at {snap}; nothing to revert')
        return
    saved=json.loads(file.read_text())
    if saved.get('reverted'):
        print('Shell snapshot already reverted')
        return
    if saved['name_dconf'] is None:
        subprocess.run(['/usr/bin/dconf','reset','/org/gnome/shell/extensions/user-theme/name'],check=True)
    else:
        subprocess.run(['/usr/bin/dconf','write','/org/gnome/shell/extensions/user-theme/name',saved['name_dconf']],check=True)
    if 'disable_user_extensions' in saved:
        restore_key(SHELL,'disable-user-extensions',saved['disable_user_extensions'])
        Gio.Settings.sync()
    restore_membership(SHELL,'enabled-extensions',UUID,saved['enabled'])
    for uid in saved.get('suppressed_user_extensions', []):
        restore_membership(SHELL,'disabled-extensions',uid,saved['disabled'])
    restore_membership(SHELL,'disabled-extensions',UUID,saved['disabled'])
    Gio.Settings.sync()
    restore_tree(THEME,snap/'previous-theme',saved['theme_existed'])
    restore_tree(EXTENSION,snap/'previous-extension',saved['extension_existed'])
    saved['reverted']=True
    write_json(file,saved)
    if not os.environ.get('MARBELL_EMBER_BACKUP_DIR'):
        (snap.parent/'latest').unlink(missing_ok=True)
    print('Shell theme and saved extension state restored; unrelated extension entries preserved. No Shell restart requested.')


if __name__ == '__main__':
    if sys.argv[1:] == ['--revert']: revert()
    elif not sys.argv[1:]: install()
    else: raise SystemExit('usage: install.py [--revert]')
