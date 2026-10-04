"""Narrow, per-component snapshots. Uses system PyGObject; never dumps unrelated keys."""
import datetime
import json
import os
import shutil
from pathlib import Path
from gi.repository import Gio, GLib


def data_home():
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))


def snapshot_dir(component, create=True):
    shared = os.environ.get('MARBELL_EMBER_BACKUP_DIR')
    if shared:
        path = Path(shared).expanduser().resolve() / component
    else:
        root = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'marbell-ember' / component
        pointer = root / 'latest'
        if pointer.exists():
            path = Path(pointer.read_text().strip())
        elif create:
            path = root / datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f')
            root.mkdir(parents=True, exist_ok=True, mode=0o700)
            pointer.write_text(str(path)+'\n')
        else:
            raise SystemExit(f'No {component} snapshot; set MARBELL_EMBER_BACKUP_DIR to the apply snapshot')
    if create: path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def settings(schema, directory=None):
    if directory:
        source = Gio.SettingsSchemaSource.new_from_directory(str(directory), Gio.SettingsSchemaSource.get_default(), False)
        obj = source.lookup(schema, True)
        if not obj: raise RuntimeError(f'Missing schema {schema}')
        return Gio.Settings.new_full(obj, None, None)
    return Gio.Settings.new(schema)


def save_key(obj, key):
    user = obj.get_user_value(key)
    return {'user': user.print_(True) if user is not None else None,
            'effective': obj.get_value(key).print_(True)}


def restore_key(obj, key, saved):
    if saved['user'] is None: obj.reset(key)
    else: obj.set_value(key, GLib.Variant.parse(None, saved['user'], None, None))


def restore_membership(obj, key, uuid, saved):
    original = GLib.Variant.parse(None, saved['effective'], None, None).unpack()
    current = obj.get_strv(key)
    merged = [x for x in current if x != uuid]
    if uuid in original:
        merged.insert(min(original.index(uuid), len(merged)), uuid)
    # Preserve unrelated extension edits made after the snapshot.
    if merged == original: restore_key(obj, key, saved)
    else: obj.set_strv(key, merged)


def backup_tree(path, backup):
    if path.exists():
        shutil.copytree(path, backup, symlinks=True)
        return True
    return False


def restore_tree(path, backup, existed):
    if path.exists(): shutil.rmtree(path)
    if existed: shutil.copytree(backup, path, symlinks=True)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')
