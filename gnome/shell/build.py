#!/usr/bin/env python3
"""Recolour the locally installed Yaru Shell theme; never vendor its generated CSS."""
import argparse
import collections
import hashlib
import json
import re
import shutil
from pathlib import Path

GLASS = '#070B16'
CORAL = '#F47853'
MAP = {
    '#131313': GLASS, '#1b1b1b': GLASS, '#202020': GLASS, '#222222': GLASS,
    '#2d2d2d': '#0B1120', '#2f2f2f': '#0B1120', '#333333': '#0B1120',
    '#353535': '#111829', '#36363a': '#0B1120', '#373737': '#111829',
    '#424242': '#1E2A44', '#424247': '#1E2A44', '#47474c': '#1E2A44',
    '#48484c': '#1E2A44', '#4a4a4f': '#26365A', '#4d4d4d': '#26365A',
    '#eef4fc': '#C9D3E3', '#c5dcf7': '#5B6B8C', '#b6e2f3': '#5B6B8C',
    '#369ad4': '#26365A', '#f34f17': CORAL, '#f37e40': CORAL,
    '#e5a50a': '#5B6B8C', '#f3af0b': '#5B6B8C', '#b2b2b4': '#5B6B8C', '#f2f2f2': '#C9D3E3', '#ffffff': '#F4F7FB',
    '#ea5b29': CORAL, '#ec6d40': CORAL, '#ee7b53': CORAL, '#ef825c': CORAL,
}
# Preserve the semantic distinctions, using the terminal's exact signal palette.
SEMANTIC = {
    '#fea320': '#F2B866', '#ffbd45': '#F2B866', '#4a4137': '#111829',
    '#fe9d96': '#E5484D', '#c7162b': '#E5484D', '#de1930': '#E5484D',
    '#e7243b': '#E5484D', '#e82d43': '#E5484D', '#a71224': '#E5484D',
    '#64cd68': '#4FD1C5', '#3ec043': '#4FD1C5',
}
TOKEN = re.compile(r'-st-accent-fg-color\b|-st-accent-color\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|\b(?:white|black|gray|red)\b')
RGBA = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(\s*,\s*[.\d]+)?\s*\)')
RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')
URL = re.compile(r'url\(["\']?([^"\')]+)["\']?\)')
COMMENT = re.compile(r'/\*.*?\*/', re.S)


def colour(value):
    if value == '-st-accent-fg-color': return GLASS
    if value == '-st-accent-color': return CORAL
    if value == 'white': return '#C9D3E3'
    if value == 'black': return GLASS
    if value == 'gray': return '#5B6B8C'
    if value == 'red': return '#E5484D'
    v = value.lower()
    if len(v) == 4: v = '#' + ''.join(c * 2 for c in v[1:])
    if v in MAP: return MAP[v]
    if v in SEMANTIC: return SEMANTIC[v]
    if v == '#000000': return v
    rgb = [int(v[i:i+2], 16) for i in (1, 3, 5)]
    if max(rgb) - min(rgb) <= 12:
        level = sum(rgb) / 3
        for limit, mapped in [(38, GLASS), (54, '#0B1120'), (65, '#111829'),
                              (78, '#1E2A44'), (105, '#26365A'), (150, '#5B6B8C'),
                              (200, '#5B6B8C'), (246, '#C9D3E3'), (256, '#F4F7FB')]:
            if level < limit: return mapped
    raise ValueError(f'Unreviewed Yaru colour {value}; review before installing this Yaru update')


def recolour(value):
    # Preserve existing alpha; black shadows remain black. No new transparency/effects.
    def rgba(m):
        rgb = tuple(map(int, m.group(1, 2, 3)))
        if rgb in ((0, 0, 0), (3, 2, 1), (128, 128, 0), (0, 0, 255), (0, 204, 204)):
            return m.group()
        mapped = colour('#%02x%02x%02x' % rgb)
        out = ', '.join(str(int(mapped[i:i+2], 16)) for i in (1, 3, 5))
        return ('rgba(' if m.group(4) else 'rgb(') + out + (m.group(4) or '') + ')'
    # Do hex first so converted rgba values are not converted a second time.
    return RGBA.sub(rgba, TOKEN.sub(lambda m: colour(m.group()), value))


def build(source, destination):
    original = source.read_text()
    source_rules = list(RULE.finditer(COMMENT.sub('', original)))
    assert source_rules and '-st-accent-color' in original, 'Not a supported Yaru Shell stylesheet'
    assets = {}
    changed = collections.Counter()

    def asset(m):
        uri = m.group(1)
        if uri in assets: return f'url("{assets[uri]}")'
        if uri.startswith('resource:///org/gnome/shell/theme/'):
            path = source.parent / uri.rsplit('/', 1)[1]
        elif not ':' in uri:
            path = source.parent / uri
            if not path.exists():
                path = Path('/usr/share/gnome-shell/extensions/ubuntu-dock@ubuntu.com') / uri
        else:
            raise ValueError(f'Unreviewed image URI: {uri}')
        if not path.is_file(): raise FileNotFoundError(path)
        relative = 'assets/' + path.name
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.svg':
            svg = path.read_text()
            # SVG colour syntax is distinct; only alter colour attributes/style literals.
            svg = re.sub(r'#[\da-fA-F]{6}\b|#[\da-fA-F]{3}\b', lambda x: colour(x.group()), svg)
            target.write_text(svg)
            if path.name == 'calendar-today.svg':
                target.with_name('calendar-today-on-coral.svg').write_text(
                    re.sub(r'fill:#[\da-fA-F]+', 'fill:' + GLASS, svg))
        else: shutil.copy2(path, target)
        assets[uri] = relative
        return f'url("{relative}")'

    def rule(m):
        selector, body = m.groups()
        def declaration(d):
            prop, value = d.groups()
            result = recolour(value)
            # Recolour existing rings/fills directly: Yaru's nested mixes dilute coral.
            if prop.strip() == 'box-shadow' and '-st-accent-color' in value and re.match(r'\s*inset 0 0 0 [12]px ', value):
                result = re.sub(r'(inset 0 0 0 [12]px ).*?(!important)?\s*$',
                                lambda x: x.group(1) + CORAL + (' !important' if x.group(2) else ''), value)
            if prop.strip() == 'box-shadow' and '#panel' in selector and 'inset 0 0 0 100px rgba(' in value:
                fill = '#26365A' if ':checked' in selector or ':active' in selector else '#1E2A44'
                result = re.sub(r'rgba\([^)]*\)', fill, value)
            if prop.strip().startswith('border') and 'rgba(' in value and any(x in value for x in ('255, 255, 255', '242, 242, 242')):
                result = re.sub(r'rgba\([^)]*\)', '#1E2A44', value)
            if result != value: changed[prop.strip()] += 1
            return prop + ':' + result + ';'
        body = re.sub(r'([\w-]+\s*):([^;{}]+);', declaration, body)
        # These upstream indicators use an opaque coral inset fill, with white text.
        if 'screen-sharing-indicator' in selector:
            body = re.sub(r'(?<![-\w])color:\s*#[\da-fA-F]+', 'color: ' + GLASS, body)
        return selector + '{' + body + '}'

    # Comments remain untouched, including the upstream licence header.
    # Mask comments rather than splitting rules: Yaru has comments INSIDE declarations.
    comments = []
    def preserve_comment(match):
        marker = f'/*__MARBELL_SAVED_COMMENT_{len(comments)}__*/'
        comments.append((marker, match.group()))
        return marker
    transformed = RULE.sub(rule, COMMENT.sub(preserve_comment, original))
    for marker, comment in comments:
        transformed = transformed.replace(marker, comment)
    transformed = URL.sub(asset, transformed)
    after_rules = list(RULE.finditer(COMMENT.sub('', transformed)))
    assert len(after_rules) == len(source_rules)
    color_props = {'-progress-bar-background', '-progress-bar-border', 'background-gradient-start', 'background-gradient-end', 'color', 'background', 'background-color', 'background-image', 'border',
                   'border-color', 'border-top', 'border-bottom', 'border-left', 'border-right',
                   'border-top-color', 'border-bottom-color', 'border-left-color', 'border-right-color',
                   'box-shadow', 'text-shadow', 'icon-shadow', 'caret-color', 'selection-background-color',
                   'selection-color', 'warning-color', 'error-color', '-arrow-background-color',
                   '-arrow-border-color', '-barlevel-background-color', '-barlevel-active-background-color',
                   '-barlevel-overdrive-color', '-barlevel-border-color', '-barlevel-active-border-color',
                   '-barlevel-overdrive-border-color', '-slider-handle-border-color', '-slider-handle-color'}
    layout = 0
    for before, after in zip(source_rules, after_rules):
        assert before.group(1) == after.group(1), 'Selector coverage changed'
        bdecl = re.findall(r'([\w-]+)\s*:([^;{}]+);', before.group(2))
        adecl = re.findall(r'([\w-]+)\s*:([^;{}]+);', after.group(2))
        assert len(bdecl) == len(adecl)
        for (bp, bv), (ap, av) in zip(bdecl, adecl):
            assert bp == ap
            if bv != av: assert bp in color_props or bp.endswith("-color"), f'Unexpected non-colour edit: {bp}'
            else: layout += 1
    assert '-st-accent-' not in transformed
    # Reviewed role overrides, kept small and separate from the generated Yaru base.
    finish = '\n' + Path(__file__).with_name('roles.css').read_text()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'gnome-shell.css').write_text(transformed + finish)
    for uri in URL.findall(transformed + finish): assert (destination / uri).is_file(), uri
    copyright_file = Path('/usr/share/doc/yaru-theme-gnome-shell/copyright')
    shutil.copy2(copyright_file, destination / 'COPYRIGHT-Yaru')
    for license_name in ('GPL-3', 'LGPL-2.1'):
        shutil.copy2(Path('/usr/share/common-licenses') / license_name, destination / license_name)
    (destination / 'DERIVATION.txt').write_text('Marbell Ember local recolour of Ubuntu Yaru.\nSource: https://github.com/ubuntu/yaru\n'
        'Generated from the installed package; original notices and licences accompany this asset.\n'
        'Modified: neutral/accent/semantic colours, relative SVG assets, and Shell font family. Layout retained.\n')
    report = {'source': str(source), 'source_sha256': hashlib.sha256(original.encode()).hexdigest(),
              'theme_sha256': hashlib.sha256((transformed+finish).encode()).hexdigest(),
              'source_rule_blocks': len(source_rules), 'preserved_rule_blocks': len(after_rules),
              'all_selectors_identical_in_order': True, 'unchanged_declarations': layout,
              'changed_colour_declarations': dict(changed),
              'accent_colour_tokens_replaced': original.count('-st-accent-color'),
              'accent_foreground_tokens_replaced': original.count('-st-accent-fg-color'),
              'assets': assets, 'semantic_colour_map': SEMANTIC,
              'alpha_policy': 'Existing Yaru alpha/shadows only; major surfaces opaque; no effects added'}
    (destination / 'build-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/usr/share/gnome-shell/theme/Yaru-dark/gnome-shell.css'))
    parser.add_argument('--output', type=Path, required=True, help='Output gnome-shell directory')
    args = parser.parse_args()
    build(args.source, args.output)
