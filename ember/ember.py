"""Marbell Ember — terminal-native graphics for the xonsh prompt.

Everything here prints on the character grid in the Ember palette:

    spark([3, 5, 2, 9, 4])                 one-line sparkline
    bars({"humidity": 71, "breaks": 12})   horizontal block chart
    gauge(0.62, "SI")                      ━━━━━━━━━━ meter
    panel("max", "any text or object")     ╭─ max ───╮ box
    table(rows, headers)                   aligned grid

`status()` feeds the live readout at the right end of the prompt.
"""
import os
import shutil
import time

INK, PANEL, DIM, TEXT, BRIGHT = "#070B16", "#1E2A44", "#5B6B8C", "#C9D3E3", "#F4F7FB"
CORAL, TEAL, AMBER, RED = "#F47853", "#4FD1C5", "#F2B866", "#E5484D"
RESET = "\x1b[0m"
_BLOCKS = "▁▂▃▄▅▆▇█"


def fg(hex_, bold=False):
    h = hex_.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\x1b[{'1;' if bold else ''}38;2;{r};{g};{b}m"


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
        print(f"{paint(str(k).ljust(lw), c)}  {paint(bar.ljust(width), c)} {paint(f'{v:g}'.rjust(vw), BRIGHT, True)}")


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


def status(buffer_text="", is_command=None):
    """Format string for xonsh's $RIGHT_PROMPT: cpu sparkline, mem meter, mode flag."""
    _sample()
    load = _cache["load"] or [0.0]
    cpu = "".join(_BLOCKS[min(7, int(v * 7.999))] for v in load).rjust(16, "▁")
    on = round(_cache["mem"] * 8)
    word = buffer_text.strip().split(" ")[0] if buffer_text.strip() else ""
    if not word:
        mode, mc = "READY", DIM
    elif is_command and is_command(word):
        mode, mc = "SHELL", TEAL
    else:
        mode, mc = "PYTHON", AMBER
    return (
        f"{{{DIM}}}cpu {{{CORAL}}}{cpu} {{{DIM}}} mem {{{TEAL}}}{'━' * on}{{{PANEL}}}{'━' * (8 - on)}"
        f"  {{{mc}}}-- {mode} --{{RESET}}"
    )
