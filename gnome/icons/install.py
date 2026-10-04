#!/usr/bin/python3
"""Install derived icons; select only the image set visually verified in Nautilus."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from gi.repository import Gio
HERE=Path(__file__).resolve().parent
sys.path.insert(1,str(HERE.parent/'shell'))
from state import data_home,snapshot_dir,settings,save_key,restore_key,backup_tree,restore_tree,write_json
from build import build
from validate import validate

TARGET=data_home()/'icons/Marbell-Ember'
INTERFACE=settings('org.gnome.desktop.interface')


def install():
    snap=snapshot_dir('icons')
    state_file=snap/'state.json'
    if state_file.exists():
        saved=json.loads(state_file.read_text())
        if saved.get('reverted'):raise SystemExit('Snapshot already reverted; choose a fresh backup directory')
    else:
        saved={'icon_theme':save_key(INTERFACE,'icon-theme'),'theme_existed':backup_tree(TARGET,snap/'previous-theme')}
        write_json(state_file,saved)
    with tempfile.TemporaryDirectory(prefix='marbell-icons-') as temporary:
        staging=Path(temporary)/'Marbell-Ember'
        build(staging,[Path('/usr/share/icons/Yaru-dark'),Path('/usr/share/icons/Yaru')])
        result=validate(staging)
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        if TARGET.exists():shutil.rmtree(TARGET)
        shutil.copytree(staging,TARGET)
    cache='/usr/bin/gtk-update-icon-cache' if Path('/usr/bin/gtk-update-icon-cache').exists() else None
    if cache:subprocess.run([cache,'--force','--ignore-theme-index',str(TARGET)],check=True)
    proof_file=HERE/'nautilus-verified.json'
    proof=json.loads(proof_file.read_text()) if proof_file.exists() else {}
    approved=result['pixels_sha256']==proof.get('pixels_sha256')
    if approved and INTERFACE.get_string('icon-theme')=='Marbell-Ember':
        # Replacing PNGs under an unchanged theme name can leave open GTK windows
        # holding textures. Emit a real theme change, then restore the chosen name.
        INTERFACE.set_string('icon-theme','Yaru-dark')
        Gio.Settings.sync()
        time.sleep(.3)
    INTERFACE.set_string('icon-theme','Marbell-Ember' if approved else 'Yaru-dark')
    Gio.Settings.sync()
    print(f'Installed {TARGET}. Snapshot: {snap}')
    if approved:print('Selected Marbell-Ember: all generated pixels match the Nautilus-verified build.')
    else:print('Left Yaru-dark selected: this Yaru build needs a fresh Nautilus visual check. See gnome/icons/README.md.')


def revert():
    snap=snapshot_dir('icons',False)
    file=snap/'state.json'
    if not file.exists():
        print(f'No icon snapshot at {snap}; nothing to revert');return
    saved=json.loads(file.read_text())
    if saved.get('reverted'):print('Icon snapshot already reverted');return
    restore_key(INTERFACE,'icon-theme',saved['icon_theme'])
    Gio.Settings.sync()
    restore_tree(TARGET,snap/'previous-theme',saved['theme_existed'])
    saved['reverted']=True
    write_json(file,saved)
    if not os.environ.get('MARBELL_EMBER_BACKUP_DIR'):(snap.parent/'latest').unlink(missing_ok=True)
    print('Previous icon theme and assets restored.')


if __name__=='__main__':
    if sys.argv[1:]==['--revert']:revert()
    elif not sys.argv[1:]:install()
    else:raise SystemExit('usage: install.py [--revert]')
