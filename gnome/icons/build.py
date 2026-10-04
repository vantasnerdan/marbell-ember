#!/usr/bin/python3
"""Recolour installed Yaru PNG folder/places assets, retaining each shipped size/mask."""
import argparse
import configparser
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, ImageChops

NAMES = {'folder','folder-open','folder-documents','folder-download','folder-music',
         'folder-pictures','folder-publicshare','folder-remote','folder-templates',
         'folder-videos','folder-dropbox','insync-folder','inode-directory','user-home','user-desktop','user-trash','user-trash-full','network-server','network-workgroup'}
# Yaru back/flap becomes coral; its front stays visibly lighter than the navy UI.
ANCHORS = [((214,69,25),(244,120,83)), ((255,127,69),(91,107,140)),
           ((255,150,102),(201,211,227)), ((174,34,14),(244,247,251)),
           ((176,73,34),(38,54,90)), ((255,255,255),(244,247,251))]
FOLDERS = NAMES - {'user-trash','user-trash-full','network-server','network-workgroup'}


def data(image):
    return image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata()


def neutral(rgb):
    value = sum(rgb) / 3
    anchors = [(0,(7,11,22)),(80,(38,54,90)),(160,(91,107,140)),
               (230,(201,211,227)),(255,(244,247,251))]
    for (low,left),(high,right) in zip(anchors,anchors[1:]):
        if value <= high:
            weight = (value-low)/(high-low)
            return tuple(round(a+(b-a)*weight) for a,b in zip(left,right))


def recolour(image, name):
    original=image.convert('RGBA')
    converted=original.copy()
    cache={}
    pixels=[]
    for r,g,b,a in data(original):
        rgb=(r,g,b)
        if rgb not in cache:
            if max(rgb)<30:
                result=rgb  # Retain upstream black shadow/edge pixels.
            elif name not in FOLDERS:
                # Trash recycling / server lights are coral. The globe's existing
                # pale connections are coral, its purple body becomes slate.
                colourful=max(rgb)-min(rgb)>20
                accent=(name=='network-workgroup' and not colourful and min(rgb)>190) or (name!='network-workgroup' and colourful)
                result=(244,120,83) if accent else neutral(rgb)
            else:
                nearest=sorted((sum((rgb[k]-s[k])**2 for k in range(3)),t) for s,t in ANCHORS)[:2]
                if nearest[0][0]==0: result=nearest[0][1]
                else:
                    weights=[1/max(d,1)**2 for d,_ in nearest]
                    result=tuple(round(sum(w*t[k] for w,(_,t) in zip(weights,nearest))/sum(weights)) for k in range(3))
            cache[rgb]=result
        pixels.append((*cache[rgb],a))
    converted.putdata(pixels)
    assert converted.getchannel('A').tobytes()==original.getchannel('A').tobytes()
    return converted


def small_emblem(image, source, section, name):
    """Recover Yaru's own 24px emblem where its 16px asset is only a plain folder."""
    if not section.startswith('16x16') or name not in FOLDERS or name in {'folder','folder-open','inode-directory','insync-folder'}:
        return []
    larger=source.parent.parent.parent/section.replace('16x16','24x24')/(name+'.png')
    plain=larger.parent/'folder.png'
    if not larger.exists() or not plain.exists(): return []
    special=Image.open(larger).convert('RGBA').convert('RGB');background=Image.open(plain).convert('RGBA').convert('RGB')
    delta=ImageChops.difference(special,background)
    mask=Image.new('L',delta.size)
    width,height=delta.size
    mask.putdata([min(255,round(max(pixel)*255/93)) if width*.18 <= i%width < width*.84 and height*.35 <= i//width < height*.88 else 0
                  for i,pixel in enumerate(data(delta))])
    mask=mask.resize(image.size,Image.Resampling.LANCZOS)
    original_alpha=image.getchannel('A')
    image.paste((244,247,251,255),(0,0,*image.size),mask)
    image.putalpha(original_alpha)
    return [{'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (larger,plain)]


def build(output, roots):
    output.mkdir(parents=True,exist_ok=True)
    entries={}
    dirs={}
    for root in reversed(roots):
        config=configparser.ConfigParser(interpolation=None,strict=False)
        config.optionxform=str
        config.read(root/'index.theme')
        for section in config.sections():
            if section.endswith(('/places','/status')):
                for source in sorted((root/section).glob('*.png')):
                    if source.stem in NAMES:
                        entries[(section,source.name)]=source
                        dirs[section]=dict(config[section])
    if not entries: raise RuntimeError('No installed Yaru folder PNG assets found')
    manifest=[]
    for (directory,name),source in sorted(entries.items()):
        target=output/directory/name
        target.parent.mkdir(parents=True,exist_ok=True)
        image=recolour(Image.open(source),source.stem)
        emblem_sources=small_emblem(image,source,directory,source.stem)
        if directory.startswith('16x16') and source.stem in FOLDERS:
            # Yaru's 16px tab is antialiased into its dark edge colour. Give this
            # existing upper flap enough solid coral pixels to survive list size.
            for y in range(round(image.height*.25)):
                for x in range(image.width):
                    alpha=image.getpixel((x,y))[3]
                    if alpha>=180:image.putpixel((x,y),(244,120,83,alpha))
        image.save(target,optimize=True)
        manifest.append({'path':f'{directory}/{name}','source':str(source),
                         'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                         'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                         'size':list(image.size),'alpha_unchanged':True,'emblem_sources':emblem_sources})
    theme=configparser.ConfigParser(interpolation=None)
    theme.optionxform=str
    theme['Icon Theme']={'Name':'Marbell Ember','Comment':'Local Yaru folder recolours; visible slate fronts, coral flaps and bright emblems.',
                         'Inherits':'Yaru-dark,Yaru,hicolor','Example':'folder','Directories':','.join(sorted(dirs))}
    for directory,values in sorted(dirs.items()): theme[directory]=values
    with (output/'index.theme').open('w') as f:theme.write(f,space_around_delimiters=False)
    shutil.copy2('/usr/share/doc/yaru-theme-icon/copyright',output/'COPYRIGHT-Yaru')
    (output/'DERIVATION.txt').write_text('Marbell Ember recolours of installed Ubuntu Yaru folder/places PNGs.\n'
        'Original icons: Sam Hewitt and Yaru contributors; https://github.com/ubuntu/yaru\n'
        'Derived icons remain CC-BY-SA-4.0; full licence in COPYRIGHT-Yaru.\n'
        'Modified RGB colours: lighter slate fronts, coral flaps, bright special-folder emblems.\n16px plain special folders borrow their existing 24px Yaru emblem. Sizes and alpha masks retained.\n')
    report={'count':len(manifest),'directories':sorted(dirs),'assets':manifest}
    (output/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Built {len(manifest)} icons across {len(dirs)} size/scale directories in {output}')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--source',action='append',type=Path,help='Theme roots, highest priority first')
    args=parser.parse_args()
    build(args.output,args.source or [Path('/usr/share/icons/Yaru-dark'),Path('/usr/share/icons/Yaru')])
