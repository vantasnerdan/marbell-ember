"""Marbell Ember — terminal-native graphics for the xonsh prompt.

Everything here prints on the character grid in the Ember palette:

    spark([3, 5, 2, 9, 4])                 one-line sparkline
    bars({"humidity": 71, "breaks": 12})   horizontal block chart
    plot(values)                           braille line chart, 2x4 dots per cell
    gauge(0.62, "SI")                      ━━━━━━━━━━ meter
    panel("max", "any text or object")     ╭─ max ───╮ box
    table(rows, headers)                   aligned grid
    show(fig)                              an image inline: a matplotlib figure, a PIL
                                           image, a .png path or PNG bytes; mpl() puts
                                           matplotlib in the palette first

`status()` feeds the live readout at the right end of the prompt.
"""
import os
import shutil
import sys
import time

INK, PANEL, DIM, TEXT, BRIGHT = "#070B16", "#1E2A44", "#687A9D", "#C9D3E3", "#F4F7FB"
CORAL, TEAL, AMBER, RED = "#F47853", "#4FD1C5", "#F2B866", "#E5484D"
RESET = "\x1b[0m"
_BLOCKS = "▁▂▃▄▅▆▇█"
# braille dot bits by (row, column) inside one cell
_DOTS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))

# The prompt readout stays quiet below these: cpu and mem only appear when they are worth
# a glance. 0 shows it always; rc.xsh reads $EMBER_CPU_HOT and $EMBER_MEM_HOT into these.
CPU_HOT, MEM_HOT = 0.70, 0.80


def _rgb(hex_):
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def fg(hex_, bold=False):
    r, g, b = _rgb(hex_)
    return f"\x1b[{'1;' if bold else ''}38;2;{r};{g};{b}m"


def _ramp(hex_, n, lo=0.50):
    """`n` colour escapes running from a banked shade of `hex_` up to the colour itself."""
    r, g, b = _rgb(hex_)
    out = []
    for i in range(n):
        k = lo + (1.0 - lo) * (i / (n - 1) if n > 1 else 1.0)
        out.append(f"\x1b[38;2;{round(r * k)};{round(g * k)};{round(b * k)}m")
    return out


def paint(s, color=TEXT, bold=False):
    return f"{fg(color, bold)}{s}{RESET}"


def _vlen(s):
    out, i = 0, 0
    while i < len(s):
        if s[i] == "\x1b":
            i = s.find("m", i) + 1 or len(s)
            continue
        out += 1
        i += 1
    return out


def sparkline(values, color=CORAL, peak=RED):
    """Return the sparkline string; the maximum is marked in `peak`."""
    vals = [float(v) for v in values]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    out = []
    for v in vals:
        ch = _BLOCKS[min(7, int((v - lo) / span * 7.999))]
        out.append(paint(ch, peak if (peak and v == hi and hi != lo) else color))
    return "".join(out)


def spark(values, label=None, color=CORAL):
    vals = list(values)
    head = paint(f"{label} ", DIM) if label else ""
    tail = paint(f"  min {min(vals):g} · max {max(vals):g} · n {len(vals)}", DIM) if vals else ""
    print(f"{head}{sparkline(vals, color)}{tail}")


def bars(data, width=None, colors=(AMBER, CORAL, TEAL, RED)):
    """Horizontal block chart from a mapping or a list of (label, value)."""
    items = list(data.items()) if hasattr(data, "items") else list(data)
    if not items:
        return
    cols = shutil.get_terminal_size((100, 30)).columns
    lw = max(len(str(k)) for k, _ in items)
    vw = max(len(f"{v:g}") for _, v in items)
    width = width or max(10, min(60, cols - lw - vw - 6))
    top = max(float(v) for _, v in items) or 1.0
    for i, (k, v) in enumerate(items):
        c = colors[i % len(colors)]
        cells = float(v) / top * width
        full, frac = int(cells), cells - int(cells)
        bar = "█" * full + (" ▏▎▍▌▋▊▉"[int(frac * 8)] if frac >= 0.125 else "")
        # each bar brightens along its length, so the longest ends at full colour
        lit = "".join(e + ch for e, ch in zip(_ramp(c, width), bar)) + RESET + " " * (width - len(bar))
        print(f"{paint(str(k).ljust(lw), c)}  {lit} {paint(f'{v:g}'.rjust(vw), BRIGHT, True)}")


def plot(values, height=6, width=None, label=None, color=CORAL):
    """Line chart in braille: every cell holds 2x4 dots, so `height` rows give 4x the
    vertical resolution of a sparkline. The series is stretched to fit `width` cells."""
    vals = [float(v) for v in values]
    if not vals:
        return
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    top, bottom = f"{hi:.3g}", f"{lo:.3g}"
    gw = max(len(top), len(bottom))
    cols = shutil.get_terminal_size((100, 30)).columns
    width = max(2, width or min(72, cols - gw - 3))
    w, h = width * 2, max(1, height) * 4
    grid = [[0] * width for _ in range(h // 4)]
    prev = None
    for x in range(w):
        pos = x * (len(vals) - 1) / (w - 1)
        i = min(int(pos), len(vals) - 1)
        v = vals[i] if i + 1 >= len(vals) else vals[i] + (vals[i + 1] - vals[i]) * (pos - i)
        y = (h - 1) // 2 if hi == lo else h - 1 - round((v - lo) / span * (h - 1))
        # join to the previous column so steep runs stay one unbroken line
        a, b = (y, y) if prev is None else (min(prev, y), max(prev, y))
        if b > a:
            a, b = (a + 1, b) if prev < y else (a, b - 1)
        for yy in range(a, b + 1):
            grid[yy // 4][x // 2] |= _DOTS[yy % 4][x % 2]
        prev = y
    rows = len(grid)
    for r, cells in enumerate(grid):
        tick = top if r == 0 else bottom if r == rows - 1 else ""
        edge = "┤" if tick else "│"
        line = "".join(chr(0x2800 + bits) if bits else " " for bits in cells).rstrip()
        print(f"{paint(tick.rjust(gw), DIM)} {paint(edge, PANEL)}{paint(line, color)}")
    head = f"{label}  " if label else ""
    print(paint(f"{' ' * gw}  {head}min {lo:g} · max {hi:g} · n {len(vals)}", DIM))


def meter(frac, cells=16, color=CORAL):
    frac = max(0.0, min(1.0, float(frac)))
    on = round(frac * cells)
    return paint("━" * on, color) + paint("━" * (cells - on), PANEL)


def gauge(frac, label="", cells=16, color=CORAL):
    print(f"{paint(label + ' ', DIM) if label else ''}{meter(frac, cells, color)} {paint(f'{float(frac) * 100:.0f}%', BRIGHT, True)}")


def panel(title, body, color=PANEL, title_color=DIM, width=None):
    """Draw `body` (str or any object) inside a rounded box with the title in the border."""
    lines = str(body).splitlines() or [""]
    inner = max([_vlen(line) for line in lines] + [len(title) + 2])
    inner = min(width or inner, shutil.get_terminal_size((100, 30)).columns - 4)
    b = fg(color)
    print(f"{b}╭─ {RESET}{paint(title, title_color)}{b} {'─' * (inner - len(title) - 1)}╮{RESET}")
    for line in lines:
        pad = " " * max(0, inner - _vlen(line))
        print(f"{b}│{RESET} {line}{pad} {b}│{RESET}")
    print(f"{b}╰{'─' * (inner + 2)}╯{RESET}")


def table(rows, headers=None):
    rows = [[str(c) for c in r] for r in rows]
    cols = list(zip(*([headers] + rows if headers else rows)))
    widths = [max(len(str(c)) for c in col) for col in cols]
    if headers:
        print("  ".join(paint(str(h).ljust(w), DIM) for h, w in zip(headers, widths)))
        print(paint("  ".join("─" * w for w in widths), PANEL))
    for r in rows:
        print("  ".join(paint(c.ljust(w), CORAL if i == 0 else TEXT) for i, (c, w) in enumerate(zip(r, widths))))


# --- images (kitty graphics protocol) ---------------------------------------------

def mpl():
    """Put matplotlib in the Ember palette. Call once, before drawing."""
    import matplotlib
    from cycler import cycler
    from matplotlib import font_manager

    # name Space Mono only where matplotlib can find it, or it warns on every label
    fonts = ["Space Mono"] if any(f.name == "Space Mono" for f in font_manager.fontManager.ttflist) else []
    matplotlib.rcParams.update({
        "figure.facecolor": INK, "axes.facecolor": INK, "savefig.facecolor": INK,
        "text.color": TEXT, "axes.labelcolor": DIM, "axes.titlecolor": BRIGHT,
        "axes.edgecolor": PANEL, "xtick.color": DIM, "ytick.color": DIM,
        "grid.color": PANEL, "axes.grid": True, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "font.family": fonts + ["monospace"],
        "axes.prop_cycle": cycler(color=[CORAL, TEAL, AMBER, "#6E9BF5", RED, "#9DB8FF"]),
    })


def _png(obj):
    import io

    if isinstance(obj, (bytes, bytearray)):
        data = bytes(obj)
    elif hasattr(obj, "savefig"):      # matplotlib figure
        buf = io.BytesIO()
        obj.savefig(buf, format="png", dpi=110, bbox_inches="tight")
        data = buf.getvalue()
    elif hasattr(obj, "save"):         # PIL image
        buf = io.BytesIO()
        obj.save(buf, format="PNG")
        data = buf.getvalue()
    else:
        with open(os.fspath(obj), "rb") as f:
            data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("show() draws PNG data: pass a matplotlib figure, a PIL image, a .png path or PNG bytes")
    return data


def show(obj, cols=None, out=None):
    """Draw an image at the prompt. Ghostty renders it inline through the kitty graphics
    protocol; `cols` scales it to that many cells wide. Terminals without the protocol
    (and multiplexers that do not pass it on) show nothing."""
    import base64

    out = out or sys.stdout
    payload = base64.standard_b64encode(_png(obj)).decode()
    ctrl = "a=T,f=100,q=2" + (f",c={int(cols)}" if cols else "") + ","
    for i in range(0, len(payload), 4096):
        more = 1 if i + 4096 < len(payload) else 0
        out.write(f"\x1b_G{ctrl}m={more};{payload[i:i + 4096]}\x1b\\")
        ctrl = ""
    out.write("\n")
    out.flush()


# --- live status (xonsh $RIGHT_PROMPT) --------------------------------------------

_cache = {"cpu": (0, 0), "load": [], "mem": 0.0, "thread": None}


def _sample_once():
    try:
        with open("/proc/stat") as f:
            p = [int(x) for x in f.readline().split()[1:8]]
        idle, total = p[3] + p[4], sum(p)
        pi, pt = _cache["cpu"]
        if pt and total > pt:
            _cache["load"] = (_cache["load"] + [1.0 - (idle - pi) / (total - pt)])[-16:]
        _cache["cpu"] = (idle, total)
        with open("/proc/meminfo") as f:
            m = dict(line.split(":")[0:2] for line in f.read().splitlines()[:5])
        _cache["mem"] = 1.0 - int(m["MemAvailable"].split()[0]) / int(m["MemTotal"].split()[0])
    except Exception:
        pass


def _sample():
    """Start the 2 s background sampler on first use (daemon thread, two tiny /proc reads)."""
    if _cache["thread"] is None:
        import threading

        def loop():
            while True:
                _sample_once()
                time.sleep(2.0)

        _cache["thread"] = threading.Thread(target=loop, daemon=True, name="ember-sampler")
        _cache["thread"].start()


def status(buffer_text="", is_command=None, flag=True):
    """Format string for xonsh's $RIGHT_PROMPT: the mode flag, plus a cpu sparkline and a
    mem meter while either is past its threshold (CPU_HOT, MEM_HOT)."""
    _sample()
    load = _cache["load"] or [0.0]
    mem = _cache["mem"]
    parts = []
    if max(load[-3:]) >= CPU_HOT:   # the last ~6 s, so it does not flicker at the edge
        cpu = "".join(_BLOCKS[min(7, int(v * 7.999))] for v in load).rjust(16, "▁")
        parts.append(f"{{{DIM}}}cpu {{{CORAL}}}{cpu}")
    if mem >= MEM_HOT:
        on = round(mem * 8)
        parts.append(f"{{{DIM}}}mem {{{AMBER if mem >= 0.80 else TEAL}}}{'━' * on}{{{PANEL}}}{'━' * (8 - on)}")
    word = buffer_text.strip().split(" ")[0] if buffer_text.strip() else ""
    if not word:
        mode, mc = "READY", DIM
    elif is_command and is_command(word):
        mode, mc = "SHELL", TEAL
    else:
        mode, mc = "PYTHON", AMBER
    if flag:
        parts.append(f"{{{mc}}}-- {mode} --")
    return "  ".join(parts) + "{RESET}" if parts else ""
