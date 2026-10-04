#!/usr/bin/python3
"""Install user assets and exact GSettings overrides; retain narrow rollback state."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

ROOT = Path(__file__).resolve().parent
PROFILE = "f4785307-0b16-4e2a-8440-5b6b8c000001"
REGISTRIES = {
    ("org.gnome.Terminal.ProfilesList", "list"),
    ("org.gnome.Ptyxis", "profile-uuids"),
}


def xdg(name, fallback):
    return Path(os.environ.get(name) or Path.home() / fallback).absolute()


def state_dir():
    return xdg("XDG_STATE_HOME", ".local/state") / "marbell-ember/gnome"


def settings(address):
    schema_id, sep, path = address.partition(":")
    schema = Gio.SettingsSchemaSource.get_default().lookup(schema_id, True)
    if schema is None:
        raise RuntimeError(f"Required GSettings schema is unavailable: {schema_id}")
    return Gio.Settings.new_full(schema, None, path if sep else None)


def parse(setting, key, value):
    return GLib.Variant.parse(setting.get_value(key).get_type(), value, None, None)


def save_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def targets():
    config = xdg("XDG_CONFIG_HOME", ".config")
    data = xdg("XDG_DATA_HOME", ".local/share")
    pairs = [
        (ROOT / "gtk-3.0/gtk.css", config / "gtk-3.0/gtk.css"),
        (ROOT / "gtk-4.0/gtk.css", config / "gtk-4.0/gtk.css"),
        (ROOT / "ptyxis/marbell-ember.palette", data / "org.gnome.Ptyxis/palettes/marbell-ember.palette"),
        (ROOT / "wallpapers/silent-seam-3440x1440.png", data / "backgrounds/marbell-ember/silent-seam-3440x1440.png"),
        (ROOT / "fontconfig/60-marbell-ember-space-mono.conf", config / "fontconfig/conf.d/60-marbell-ember-space-mono.conf"),
    ]
    # The active Brave Snap has a separate config home and an older GTK4.
    brave = Path.home() / "snap/brave/current"
    if brave.is_dir() and os.environ.get("GSETTINGS_BACKEND") != "memory":
        pairs.append((ROOT / "brave/gtk.css", brave / ".config/gtk-4.0/gtk.css"))
    return pairs


def planned_settings():
    document = json.loads((ROOT / "settings.json").read_text())
    wallpaper = targets()[3][1].as_uri()
    rows = []
    for address, keys in document["settings"].items():
        setting = settings(address)
        schema = setting.props.settings_schema
        for key, value in keys.items():
            # A URI is constructed as a GVariant string, never shell-expanded.
            desired = GLib.Variant("s", wallpaper) if value == "'${WALLPAPER_URI}'" else parse(setting, key, value)
            if not schema.get_key(key).range_check(desired):
                raise RuntimeError(f"Out-of-range value: {address} {key}")
            if not setting.is_writable(key):
                raise RuntimeError(f"Setting is locked: {address} {key}")
            before = setting.get_user_value(key)
            rows.append({"address": address, "key": key,
                         "before": None if before is None else before.print_(True),
                         "effective_before": setting.get_value(key).print_(True),
                         "after": desired.print_(True),
                         "registry": (address, key) in REGISTRIES})
    # Populate relocatable profile keys before publishing the profile in its list.
    return sorted(rows, key=lambda r: 0 if ":/" in r["address"] else 1)


def snapshot_files(backup, pairs):
    rows = []
    (backup / "files").mkdir()
    for i, (source, target) in enumerate(pairs):
        if not source.is_file():
            raise RuntimeError(f"Missing source asset: {source}")
        origin = str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source.relative_to(backup))
        row = {"path": str(target), "source": origin,
               "before": "absent", "installed_sha256": digest(source)}
        if target.is_symlink():
            row.update(before="symlink", link=os.readlink(target))
        elif target.exists():
            if not target.is_file():
                raise RuntimeError(f"Not a regular file: {target}")
            name = f"files/{i}"
            shutil.copy2(target, backup / name)
            row.update(before="file", payload=name, mode=stat.S_IMODE(target.stat().st_mode))
        rows.append(row)
    return rows


def install_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    # Replace a symlink itself, never overwrite its external target.
    temp = target.with_name(target.name + ".marbell-ember-tmp")
    if temp.exists() or temp.is_symlink():
        raise RuntimeError(f"Temporary path already exists: {temp}")
    shutil.copyfile(source, temp)
    temp.chmod(0o644)
    temp.replace(target)


def apply(args):
    rows = planned_settings()  # Preflight before any changes to live settings.
    fallback = subprocess.check_output(
        ["/usr/bin/fc-match", "MesloLGM Nerd Font Mono", "-f", "%{family}"], text=True)
    if "MesloLGM Nerd Font Mono" not in fallback.split(","):
        raise RuntimeError("Required fallback font is unavailable: MesloLGM Nerd Font Mono (no fonts were downloaded)")
    for source, _ in targets():
        if not source.is_file():
            raise RuntimeError(f"Missing source asset: {source}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = state_dir() / "backups" / stamp
    backup.mkdir(parents=True, mode=0o700)
    spec = importlib.util.spec_from_file_location("ember_gtk_builder", ROOT / "gtk-3.0/build_theme.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    generated = builder.build(backup / "generated/theme")
    pairs = targets() + [(source, xdg("XDG_DATA_HOME", ".local/share") / "themes/Marbell-Ember" / source.relative_to(generated))
                         for source in sorted(generated.rglob("*")) if source.is_file()]
    manifest = {"version": 1, "created": stamp, "status": "snapshot",
                "settings": rows, "files": snapshot_files(backup, pairs), "components": []}
    save_json(backup / "manifest.json", manifest)
    save_json(state_dir() / "latest.json", {"backup": str(backup)})
    print(f"Snapshot: {backup}", flush=True)
    try:
        for source, target in pairs:
            install_file(source, target)
        for row in rows:
            setting = settings(row["address"])
            value = parse(setting, row["key"], row["after"])
            if row["registry"]:
                # Re-read just before writing; never reuse the audited list.
                current = list(setting.get_strv(row["key"]))
                additions = [p for p in value.unpack() if p not in current]
                value = GLib.Variant("as", current + additions)
                row["added"] = additions
                row["after"] = value.print_(True)
                save_json(backup / "manifest.json", manifest)
            if not setting.set_value(row["key"], value):
                raise RuntimeError(f"Could not set {row['address']} {row['key']}")
        Gio.Settings.sync()
        for row in rows:
            actual = settings(row["address"]).get_value(row["key"])
            expected = parse(settings(row["address"]), row["key"], row["after"])
            if actual != expected:
                raise RuntimeError(f"Readback mismatch: {row['address']} {row['key']}: {actual.print_(True)}")
            row["verified_after"] = actual.print_(True)
        if not args.settings_only:
            for component in ("shell", "icons"):
                installer = ROOT / component / "install.sh"
                if installer.is_file() and os.access(installer, os.X_OK):
                    manifest["components"].append(component)
                    save_json(backup / "manifest.json", manifest)
                    subprocess.run(["bash", str(installer)], check=True,
                                   env={**os.environ, "MARBELL_EMBER_BACKUP_DIR": str(backup)})
        manifest["status"] = "applied"
        save_json(backup / "manifest.json", manifest)
        print("Applied GTK CSS, wallpaper, desktop settings and terminal profiles.")
        print("Verified live: " + ", ".join(f"{k}={settings('org.gnome.desktop.interface').get_value(k).print_(True)}"
                                          for k in ("gtk-theme", "color-scheme", "font-name")))
        print(f"Revert: {ROOT / 'revert.sh'} '{backup}'")
    except BaseException:
        Gio.Settings.sync()
        manifest["status"] = "incomplete"
        save_json(backup / "manifest.json", manifest)
        print(f"Partial apply; restore with: {ROOT / 'revert.sh'} '{backup}'", file=sys.stderr)
        raise


def resolve_backup(value):
    if value:
        return Path(value).expanduser().resolve()
    return Path(json.loads((state_dir() / "latest.json").read_text())["backup"])


def components_for(backup, manifest):
    # Also discover snapshots written independently by the parallel component
    # installers. Do not rewrite their original state or the desktop manifest.
    return [name for name in ("shell", "icons")
            if name in manifest.get("components", []) or (backup / name / "state.json").is_file()]


def rollback_steps(args):
    directory = (state_dir() / "backups").resolve()
    if args.through and not args.snapshot:
        raise RuntimeError("--through requires the oldest snapshot to restore")
    if args.snapshot:
        backup = resolve_backup(args.snapshot)
        if args.through:
            if backup.parent != directory:
                raise RuntimeError("--through requires a snapshot from this user's state directory")
            candidates = [p for p in sorted(directory.iterdir(), reverse=True) if p.name >= backup.name]
        else:
            candidates = [backup]
    else:
        # A repeated apply is one installation round. Default rollback reaches
        # its original state, not merely the previous already-themed iteration.
        candidates = sorted(directory.iterdir(), reverse=True) if directory.exists() else []
    result = []
    for backup in candidates:
        file = backup / "manifest.json"
        if not file.is_file():
            if args.snapshot and not args.through:
                raise RuntimeError(f"Missing desktop snapshot: {file}")
            continue
        manifest = json.loads(file.read_text())
        if manifest.get("version") != 1:
            raise RuntimeError(f"Unsupported snapshot format: {file}")
        components = [] if args.settings_only else components_for(backup, manifest)
        pending = []
        for name in reversed(components):
            state = backup / name / "state.json"
            if not state.is_file():
                raise RuntimeError(f"Missing component snapshot: {state}")
            saved = json.loads(state.read_text())
            if saved.get("reverted"):
                continue
            restorer = ROOT / name / "revert.sh"
            if not restorer.is_file() or not os.access(restorer, os.X_OK):
                raise RuntimeError(f"Component has no executable revert.sh: {name}")
            pending.append((name, saved))
        if manifest.get("status") != "reverted" or pending:
            result.append((backup, manifest, pending))
    return result


def validate_rollback(steps, force):
    # Simulate file restoration newest first. Comparing every old snapshot to
    # today's files would incorrectly flag legitimate later apply iterations.
    simulated = {}
    for backup, manifest, _ in steps:
        if manifest.get("status") == "reverted":
            continue
        for row in manifest["files"]:
            target = Path(row["path"])
            if str(target) not in simulated:
                if target.is_symlink():
                    simulated[str(target)] = ("symlink", os.readlink(target))
                elif target.is_file():
                    simulated[str(target)] = ("file", digest(target))
                elif target.exists():
                    raise RuntimeError(f"Not a regular file: {target}")
                else:
                    simulated[str(target)] = ("absent", None)
            kind, value = simulated[str(target)]
            if kind != "absent" and (kind != "file" or value != row["installed_sha256"]) and not force:
                raise RuntimeError(f"File changed since apply: {target}; use --force to restore its snapshot")
            if row["before"] == "file":
                simulated[str(target)] = ("file", digest(backup / row["payload"]))
            elif row["before"] == "symlink":
                simulated[str(target)] = ("symlink", row["link"])
            else:
                simulated[str(target)] = ("absent", None)


def revert(args):
    steps = rollback_steps(args)
    validate_rollback(steps, args.force)
    if args.dry_run:
        final_keys = {}
        for backup, manifest, components in steps:
            if manifest.get("status") != "reverted":
                print(f"Would restore {backup.name}: {len(manifest['settings'])} keys, {len(manifest['files'])} files")
                for row in manifest["settings"]:
                    final_keys[(row["address"], row["key"])] = row["before"]
            for name, saved in components:
                print(f"Would call {name}/revert.sh with MARBELL_EMBER_BACKUP_DIR={backup}")
                if name == "shell":
                    print(f"  user-theme name: {saved['name_dconf']!r}; global mute: {saved.get('disable_user_extensions')}")
                    print(f"  restore extension memberships from enabled={saved['enabled']}, disabled={saved['disabled']}")
                else:
                    print(f"  icon-theme: {saved['icon_theme']}")
        print("Final desktop key states (None means reset to default; profile lists preserve later additions):")
        for (address, key), value in sorted(final_keys.items()):
            print(f"  {address} {key}: {value}")
        print(f"Dry run validated {len(steps)} snapshots; no keys, files or snapshots changed.")
        return
    for backup, manifest, components in steps:
        revert_one(backup, manifest, components, args)
    if not steps:
        print("Nothing remains to revert.")


def revert_one(backup, manifest, components, args):
    # Detect edits before restoring anything; --force explicitly restores the snapshot.
    for row in manifest["files"] if manifest.get("status") != "reverted" else []:
        target = Path(row["path"])
        if target.exists() or target.is_symlink():
            changed = target.is_symlink() or not target.is_file() or digest(target) != row["installed_sha256"]
            if changed and not args.force:
                raise RuntimeError(f"File changed since apply: {target}; use --force to restore its snapshot")
    for component, _ in components:
        subprocess.run(["bash", str(ROOT / component / "revert.sh")], check=True,
                       env={**os.environ, "MARBELL_EMBER_BACKUP_DIR": str(backup)})
    if manifest.get("status") == "reverted":
        return
    for row in reversed(manifest["settings"]):
        setting = settings(row["address"])
        key = row["key"]
        if row["registry"]:
            # Keep unrelated profiles created since apply. Revert this install's additions only.
            current = list(setting.get_strv(key))
            remaining = [p for p in current if p not in row.get("added", [])]
            original = parse(setting, key, row["effective_before"]).unpack()
            if remaining != original:
                setting.set_strv(key, remaining)
                continue
        if row["before"] is None:
            setting.reset(key)
        else:
            if not setting.set_value(key, parse(setting, key, row["before"])):
                raise RuntimeError(f"Could not restore {row['address']} {key}")
    Gio.Settings.sync()
    for row in manifest["files"]:
        target = Path(row["path"])
        if target.exists() or target.is_symlink():
            target.unlink()
        if row["before"] == "file":
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup / row["payload"], target)
            target.chmod(row["mode"])
        elif row["before"] == "symlink":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(row["link"])
    manifest["status"] = "reverted"
    save_json(backup / "manifest.json", manifest)
    print(f"Restored keys and files from {backup}")
    print("Relaunch affected GTK applications to reload their CSS.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ap = sub.add_parser("apply")
    ap.add_argument("--settings-only", action="store_true", help="Skip optional Shell/icon component installers")
    rp = sub.add_parser("revert")
    rp.add_argument("snapshot", nargs="?", help="One timestamped snapshot (default: all pending snapshots, newest first)")
    rp.add_argument("--settings-only", action="store_true", help="Restore only this installer's keys and files")
    rp.add_argument("--force", action="store_true", help="Restore files even if edited since apply")
    rp.add_argument("--through", action="store_true", help="Restore newer snapshots first, then the specified snapshot")
    rp.add_argument("--dry-run", action="store_true", help="Validate and print the full restore plan without changing anything")
    args = parser.parse_args()
    if args.command == "revert" and args.dry_run:
        revert(args)
        return
    os.umask(0o077)
    state_dir().mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state_dir() / "install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        (apply if args.command == "apply" else revert)(args)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, GLib.Error, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
