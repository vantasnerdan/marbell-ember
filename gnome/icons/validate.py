#!/usr/bin/python3
"""Check GTK's real resolver at every generated size/scale and inherited app icons."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
from PIL import Image


def signature(root):
    manifest=json.loads((root/'build-report.json').read_text())
    digest=hashlib.sha256()
    for item in manifest['assets']:
        image=Image.open(root/item['path']).convert('RGBA')
        digest.update(item['path'].encode()+str(image.size).encode()+image.tobytes())
    digest.update((root/'index.theme').read_bytes())
    return digest.hexdigest()


def validate(root):
    Gtk.init()
    theme=Gtk.IconTheme.new()
    theme.set_search_path([str(root.parent),'/usr/share/icons','/usr/share/pixmaps'])
    theme.set_theme_name(root.name)
    config=configparser.ConfigParser()
    config.read(root/'index.theme')
    manifest=json.loads((root/'build-report.json').read_text())
    for item in manifest['assets']:
        relative=Path(item['path'])
        section=str(relative.parent)
        size=config.getint(section,'Size')
        scale=config.getint(section,'Scale',fallback=1)
        icon=theme.lookup_icon(relative.stem,None,size,scale,Gtk.TextDirection.NONE,Gtk.IconLookupFlags(0))
        resolved=icon.get_file().get_path() if icon.get_file() else ''
        assert Path(resolved).resolve()==(root/relative).resolve(), (relative,resolved)
        assert Image.open(root/relative).size==(size*scale,size*scale)
    for name in ['org.gnome.Nautilus','folder-symbolic','user-trash-symbolic']:
        icon=theme.lookup_icon(name,None,48,1,Gtk.TextDirection.NONE,Gtk.IconLookupFlags(0))
        assert icon.get_file(),name
        assert not icon.get_file().get_basename().startswith('image-missing'),name
    result={'gtk_lookup_count':len(manifest['assets']),'inherited_icons_resolve':True,'pixels_sha256':signature(root)}
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('theme',type=Path)
    args=parser.parse_args()
    validate(args.theme.resolve())
