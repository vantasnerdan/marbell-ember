#!/usr/bin/python3
"""Render unscaled icon rows at real 16/24/32/48px sizes on Ember glass."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NAMES=['folder','user-home','user-desktop','folder-documents','folder-download',
       'folder-music','folder-pictures','folder-videos','user-trash','user-trash-full',
       'network-server','network-workgroup']


def render(theme,output):
    width=64+len(NAMES)*76
    image=Image.new('RGB',(width,428),'#070B16')
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
    for row,size in enumerate((16,24,32,48)):
        y=20+row*100
        draw.text((6,y+18),str(size)+' px',fill='#C9D3E3',font=font)
        for col,name in enumerate(NAMES):
            category='status' if name=='user-trash-full' else 'places'
            path=theme/f'{size}x{size}'/category/(name+'.png')
            icon=Image.open(path).convert('RGBA')
            x=64+col*76
            image.paste(icon,(x+(64-size)//2,y),icon)
            label=name.replace('folder-','').replace('user-','').replace('network-','')
            draw.text((x,y+58),label,fill='#C9D3E3',font=font)
        draw.line((6,y+86,width-6,y+86),fill='#1E2A44')
    output.parent.mkdir(parents=True,exist_ok=True)
    image.save(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('theme',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    render(args.theme,args.output)
