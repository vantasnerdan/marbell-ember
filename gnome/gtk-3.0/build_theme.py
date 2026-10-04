#!/usr/bin/python3
"""Build a named GTK/Metacity theme from installed Yaru-dark assets.

Only configuration/theme assets are generated; no Ubuntu files are changed.
Derived stylesheets and their license notices stay on the user's machine.
"""
import argparse
import colorsys
import json
from pathlib import Path
import re
import shutil

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio

BASE = Path("/usr/share/themes/Yaru-dark")
ROOT = Path(__file__).resolve().parents[1]


def recolor_hex(match):
    token = match.group(0)
    raw = token[1:]
    if len(raw) == 3:
        raw = "".join(c * 2 for c in raw)
    if len(raw) not in (6, 8):
        return token
    rgb = [int(raw[i:i+2], 16) for i in (0, 2, 4)]
    hue, sat, value = colorsys.rgb_to_hsv(*(c/255 for c in rgb))
    # Map neutral surfaces and semantic hues into the Ember palette.
    if max(rgb) - min(rgb) < 14:
        level = sum(rgb) / 3
        color = ("#070B16" if level < 28 else "#0B1120" if level < 43 else
                 "#111829" if level < 60 else "#1E2A44" if level < 90 else
                 "#5B6B8C" if level < 155 else "#C9D3E3" if level < 242 else "#F4F7FB")
    elif 0.015 < hue < 0.095 and sat > .35:
        color = "#F47853" if value > .65 else "#26365A"
    elif sat > .35 and (hue <= .015 or hue >= .95):
        color = "#E5484D" if value > .45 else "#111829"
    elif sat > .35 and .095 <= hue < .19:
        color = "#F2B866" if value > .45 else "#111829"
    elif sat > .35 and .19 <= hue < .49:
        color = "#4FD1C5" if value > .45 else "#111829"
    elif sat > .35 and .49 <= hue < .72:
        color = "#6E9BF5" if value > .45 else "#111829"
    else:
        return token
    return color + (raw[6:] if len(raw) == 8 else "")


def recolor(text):
    text = re.sub(r"#[0-9a-fA-F]{3,8}\b", recolor_hex, text)
    # Generated Yaru also uses rgb()/rgba() for some neutral borders/shadows.
    def rgb(match):
        r, g, b = map(int, match.group(2, 3, 4))
        token = recolor_hex(re.match(r".*", f"#{r:02x}{g:02x}{b:02x}"))
        values = ", ".join(str(int(token[i:i+2], 16)) for i in (1, 3, 5))
        return match.group(1) + "(" + values + (match.group(5) or "") + ")"
    return re.sub(r"\b(rgb|rgba)\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(\s*,\s*[\d.]+)?\s*\)", rgb, text)


def leaves(resource, prefix):
    for name in resource.enumerate_children(prefix, Gio.ResourceLookupFlags.NONE):
        path = prefix + name
        if name.endswith("/"):
            yield from leaves(resource, path)
        else:
            yield path


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    report = {}
    for version in ("3.0", "4.0"):
        prefix = f"/com/ubuntu/themes/Yaru-dark/{version}/"
        resource = Gio.Resource.load(str(BASE / f"gtk-{version}/gtk.gresource"))
        output = destination / f"gtk-{version}"
        output.mkdir()
        css = recolor(bytes(resource.lookup_data(prefix + "gtk.css", Gio.ResourceLookupFlags.NONE).get_data()).decode())
        css = css.replace("resource://" + prefix, "")
        overrides = (ROOT / f"gtk-{version}/gtk.css").read_text()
        css = "/* Marbell Ember, generated from installed Yaru-dark. See COPYRIGHT. */\n" + css + "\n" + overrides
        for filename in ("gtk.css", "gtk-dark.css"):
            (output / filename).write_text(css)
        count = 0
        for path in leaves(resource, prefix + "assets/"):
            asset = output / path.removeprefix(prefix)
            asset.parent.mkdir(parents=True, exist_ok=True)
            content = bytes(resource.lookup_data(path, Gio.ResourceLookupFlags.NONE).get_data())
            asset.write_bytes(recolor(content.decode()).encode() if asset.suffix == ".svg" else content)
            count += 1
        shutil.copyfile("/usr/share/doc/yaru-theme-gtk/copyright", output / "COPYRIGHT")
        report[version] = {"source": str(BASE / f"gtk-{version}/gtk.gresource"), "assets": count}
    metacity = destination / "metacity-1"
    metacity.mkdir()
    for source in (BASE / "metacity-1").iterdir():
        target = metacity / source.name
        if source.is_symlink():
            target.symlink_to(source.readlink())
        else:
            target.write_text(recolor(source.read_text()))
    shutil.copyfile("/usr/share/doc/yaru-theme-gtk/copyright", metacity / "COPYRIGHT")
    (destination / "index.theme").write_text(
        "[Desktop Entry]\nName=Marbell Ember\nType=X-GNOME-Metatheme\n"
        "Comment=Opaque navy and coral theme generated from installed Yaru-dark\n"
        "[X-GNOME-Metatheme]\nGtkTheme=Marbell-Ember\nMetacityTheme=Marbell-Ember\n")
    (destination / "gtk-build.json").write_text(json.dumps(report, indent=2) + "\n")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Empty staging directory")
    build(parser.parse_args().destination)
