# Marbell Ember — xonsh
# Ghostty starts this shell directly; the login shell and $SHELL stay bash.
import os
import sys
from pathlib import Path

# --- environment ---------------------------------------------------------------
# Ghostty starts xonsh directly, so whatever your ~/.bashrc exports (PATH entries,
# CUDA, API env files) goes in ~/.config/xonsh/local.xsh, which is yours and untracked.
_home = Path.home()
if str(_home / ".local/bin") not in $PATH:
    $PATH.insert(0, str(_home / ".local/bin"))
_local = _home / ".config/xonsh/local.xsh"
if _local.exists():
    source @(str(_local))

def _have(cmd):
    """True if `cmd` is on PATH. Every optional tool below is guarded with this, so the
    same rc works on a machine that has only xonsh."""
    import shutil
    return shutil.which(cmd, path=os.pathsep.join($PATH)) is not None

# --- shell behaviour -----------------------------------------------------------
$XONSH_HISTORY_BACKEND = "sqlite"
$HISTCONTROL = {"ignoredups", "ignorespace"}
$XONSH_HISTORY_SIZE = (100000, "commands")
$AUTO_CD = True
$XONSH_PROMPT_AUTO_SUGGEST = True
$AUTO_SUGGEST_IN_COMPLETIONS = True
$COMPLETIONS_CONFIRM = True
$COMPLETIONS_MENU_ROWS = 10
$XONSH_AUTOPAIR = True
$XONSH_CTRL_BKSP_DELETION = True
$XONSH_SHOW_TRACEBACK = False
$XONSH_SUBPROC_RAISE_ERROR = False   # a failing command is a red prompt, not a Python exception
$MOUSE_SUPPORT = False
$EDITOR = ${...}.get("EDITOR", "nano")
$PROMPT_TOOLKIT_COLOR_DEPTH = "DEPTH_24_BIT"
$COLORTERM = "truecolor"
$TITLE = "{current_job:{} · }{cwd}"
$MULTILINE_PROMPT = "│"
$XONSH_PROMPT_CURSOR_SHAPE = "block"   # steady: the glass shader breathes a halo around it instead
$EMBER_CALLSIGN = ${...}.get("EMBER_CALLSIGN", "MARBELL")
# Once a line is run its prompt collapses to a bare ❯, so the scrollback is commands and
# output. Set $EMBER_TRANSIENT = "0" in local.xsh to keep the full bar on every line.
$EMBER_TRANSIENT = ${...}.get("EMBER_TRANSIENT", "1")

# --- Ember colours for the line editor ------------------------------------------
$XONSH_COLOR_STYLE = "default"
$XONSH_STYLE_OVERRIDES.update({
    "Token.Text": "#C9D3E3",
    "Token.Name": "#C9D3E3",
    "Token.Name.Builtin": "#4FD1C5",
    "Token.Name.Function": "#F4F7FB",
    "Token.Name.Class": "bold #F4F7FB",
    "Token.Name.Namespace": "#C9D3E3",
    "Token.Name.Variable": "#FF9A7B",
    "Token.Name.Constant": "#FF9A7B",
    "Token.Name.Decorator": "#F47853",
    "Token.Keyword": "#F47853",
    "Token.Keyword.Constant": "#FF9A7B",
    "Token.Keyword.Namespace": "#F47853",
    "Token.Operator": "#5CC8F0",
    "Token.Operator.Word": "#F47853",
    "Token.Punctuation": "#687A9D",
    "Token.Literal.String": "#F2B866",
    "Token.Literal.String.Escape": "#FFD08A",
    "Token.Literal.Number": "#FF9A7B",
    "Token.Comment": "italic #687A9D",
    "Token.Error": "#E5484D",
    "Token.PTK.AutoSuggestion": "#687A9D",
    "Token.PTK.Aborting": "#687A9D",
    "Token.PTK.CompletionMenu": "bg:#111829 #C9D3E3",
    "Token.PTK.CompletionMenu.Completion": "bg:#111829 #C9D3E3",
    "Token.PTK.CompletionMenu.Completion.Current": "bg:#F47853 #070B16 bold",
    "Token.PTK.CompletionMenu.Meta.Completion": "bg:#0C1220 #687A9D",
    "Token.PTK.CompletionMenu.Meta.Completion.Current": "bg:#1E2A44 #F4F7FB",
    "Token.PTK.Scrollbar.Background": "bg:#111829",
    "Token.PTK.Scrollbar.Button": "bg:#F47853",
    "Token.PTK.MatchingBracket.Cursor": "bold #F47853",
    "Token.PTK.MatchingBracket.Other": "bold #4FD1C5",
})

# --- tool colours ------------------------------------------------------------------
$EZA_COLORS = ":".join([
    "di=1;38;2;157;184;255", "ex=38;2;79;209;197", "ln=38;2;92;200;240", "or=38;2;229;72;77",
    "ur=38;2;104;122;157", "uw=38;2;104;122;157", "ux=38;2;79;209;197", "ue=38;2;79;209;197",
    "gr=38;2;104;122;157", "gw=38;2;104;122;157", "gx=38;2;104;122;157",
    "tr=38;2;104;122;157", "tw=38;2;242;184;102", "tx=38;2;104;122;157",
    "sn=38;2;244;120;83", "sb=38;2;104;122;157", "nb=38;2;104;122;157", "nk=38;2;201;211;227",
    "nm=38;2;242;184;102", "ng=38;2;244;120;83", "nt=38;2;229;72;77",
    "uu=38;2;104;122;157", "un=38;2;242;184;102", "gu=38;2;104;122;157", "da=38;2;104;122;157",
    "ga=38;2;79;209;197", "gm=38;2;242;184;102", "gd=38;2;229;72;77", "gv=38;2;92;200;240", "gt=38;2;244;120;83",
    "xx=38;2;30;42;68", "hd=4;38;2;104;122;157", "lp=38;2;92;200;240",
    "*.md=38;2;244;247;251", "*.json=38;2;242;184;102", "*.toml=38;2;242;184;102", "*.py=38;2;255;154;123",
])
$FZF_DEFAULT_OPTS = " ".join([
    "--style=full", "--layout=reverse", "--height=60%", "--border=rounded", "--info=inline-right",
    "--prompt='❯ '", "--pointer='▌'", "--marker='●'", "--highlight-line",
    "--color=bg:-1,bg+:#111829,fg:#C9D3E3,fg+:#F4F7FB,hl:#F47853,hl+:#FF9A7B,gutter:-1",
    "--color=info:#687A9D,prompt:#F47853,pointer:#F47853,marker:#4FD1C5,spinner:#F2B866",
    "--color=header:#687A9D,border:#1E2A44,label:#687A9D,query:#F4F7FB,separator:#1E2A44,scrollbar:#F47853",
    "--color=list-border:#1E2A44,input-border:#F47853,preview-border:#1E2A44,header-border:#1E2A44",
])
$BAT_THEME = "ansi"
if _have("bat"):
    $MANPAGER = "sh -c 'col -bx | bat -l man -p'"
    $MANROFFOPT = "-c"

# --- aliases ------------------------------------------------------------------------
if _have("eza"):
    _EZA = ["eza", "--icons=auto", "--group-directories-first"]

    def _ls(args):
        """eza for everyday use; real ls when the flags are ones eza reads differently
        (ls -ltr, -S, -h ...), so muscle memory and pasted commands keep working."""
        import re
        if any(re.match(r"^-[A-Za-z]*[tSXcuvChHkqQNbpwxm]", a) for a in args if not a.startswith("--")):
            return __xonsh__.subproc_captured_hiddenobject(["/bin/ls", "--color=auto", *args]).rtn
        return __xonsh__.subproc_captured_hiddenobject([*_EZA, *args]).rtn   # .rtn: a failed ls marks the prompt

    aliases["ls"] = _ls
    aliases["ll"] = _EZA + ["-l", "--git", "--time-style=relative", "--no-user"]
    aliases["la"] = _EZA + ["-la", "--git", "--time-style=relative"]
    aliases["lt"] = _EZA + ["--tree", "--level=2"]
else:
    aliases["ls"] = "ls --color=auto"
    aliases["ll"] = "ls --color=auto -lh"
    aliases["la"] = "ls --color=auto -lAh"
if _have("bat"):
    aliases["cat"] = "bat --paging=never"
if _have("btop"):
    aliases["top"] = "btop"
if _have("fastfetch"):
    aliases["boot"] = "fastfetch"
aliases["grep"] = "grep --color=auto"

# bash habits that would otherwise be "command not found"
def _export(args):
    """export NAME=value [NAME2=value2 ...]"""
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            ${...}[k] = v
    return 0

def _unset(args):
    for k in args:
        ${...}.pop(k, None)
    return 0

aliases["export"] = _export
aliases["unset"] = _unset

# --- ember: Python graphics at the prompt (spark, bars, gauge, panel, table) -------------
sys.path.insert(0, str(_home / ".config/ember"))
import ember
from ember import spark, bars, plot, gauge, panel, table, show
# the readout's thresholds; set either to "0" in local.xsh to show cpu / mem always
ember.CPU_HOT = float(${...}.get("EMBER_CPU_HOT", ember.CPU_HOT))
ember.MEM_HOT = float(${...}.get("EMBER_MEM_HOT", ember.MEM_HOT))

_EMBER_LIVE = True
_cmd_cache = {}   # first word -> is it a command; the readout asks on every key

def _is_cmd(word):
    if word not in _cmd_cache:
        _cmd_cache[word] = word in aliases or bool(__xonsh__.commands_cache.locate_binary(word))
    return _cmd_cache[word]

@events.on_pre_prompt
def _ember_forget_cmds(**kw):
    _cmd_cache.clear()   # a command installed by the last line is found on the next one

def _ember_line_done():
    """True once the line being edited has been accepted (prompt_toolkit's last repaint)."""
    try:
        return __xonsh__.shell.shell.prompter.app.is_done
    except Exception:
        return False

def _ember_status():
    try:
        app = __xonsh__.shell.shell.prompter.app
        if app.is_done:
            return ""  # the line has been run: leave nothing behind in the scrollback
        text = app.current_buffer.text
    except Exception:
        text = ""
    try:
        return ember.status(text, _is_cmd, flag=_EMBER_LIVE)
    except Exception:
        return ""

# --- prompt, jumps, history search -----------------------------------------------------
$RIGHT_PROMPT = _ember_status
if _have("starship"):
    execx($(starship init xonsh))
    # live readout (cpu, mem, SHELL / PYTHON flag) at the top right of the prompt;
    # prompt_toolkit hides it when the typed text reaches it and once the line is run
    $RIGHT_PROMPT = _ember_status

    # The readout has to repaint on every key (for the SHELL / PYTHON flag), which makes
    # xonsh re-evaluate $PROMPT on every key too. Starship is a subprocess, so run it once
    # per prompt and hand back the cached string after that.
    # Starship is called with plain subprocess rather than xonsh's $(...), so it never
    # registers as the "current job" and leaks into the terminal title.
    _STARSHIP = __import__("shutil").which("starship", path=os.pathsep.join($PATH))

    def _starship_prompt():
        import subprocess
        hist = __xonsh__.history
        status = hist.rtns[-1] if len(hist.rtns) else 0
        ts = hist.tss[-1] if len(hist.tss) else None
        duration = round((ts[1] - ts[0]) * 1000) if ts else 0
        jobs = sum(1 for j in __xonsh__.all_jobs.values() if j["obj"] and j["obj"].poll() is None)
        try:
            width = os.get_terminal_size().columns
        except OSError:
            width = 100
        r = subprocess.run([_STARSHIP, "prompt", f"--status={status}", f"--jobs={jobs}", f"--cmd-duration={duration}",
                            f"--terminal-width={width}"], capture_output=True, text=True, env=${...}.detype())
        return r.stdout

    _prompt_cache = {}

    @events.on_pre_prompt
    def _ember_new_prompt(**kw):
        _prompt_cache.clear()

    def _ember_prompt():
        if $EMBER_TRANSIENT != "0" and _ember_line_done():
            # like the bar's own ❯: red when the command before this one failed. Raw escapes,
            # as Starship sends: a colour name xonsh has not seen yet is not styled in time
            # for this last repaint.
            rtns = __xonsh__.history.rtns
            return "\n" + ember.fg(ember.RED if len(rtns) and rtns[-1] else ember.CORAL, bold=True) + "❯" + ember.RESET + " "
        if "p" not in _prompt_cache:
            _prompt_cache["p"] = _starship_prompt()
        return _prompt_cache["p"]

    $PROMPT = _ember_prompt
    $UPDATE_PROMPT_ON_KEYPRESS = True
else:
    # no Starship on this machine: a native prompt in the same colours. It is evaluated
    # once per prompt, so the readout shows cpu and mem but no live SHELL / PYTHON flag.
    _EMBER_LIVE = False
    $PROMPT = ("\n{BACKGROUND_#F47853}{BOLD_#070B16} " + $EMBER_CALLSIGN + " {BACKGROUND_#1E2A44}{BOLD_#F4F7FB} {short_cwd} "
               "{RESET}{#4FD1C5}{curr_branch: {}}{RESET}\n{BOLD_#F47853}❯{RESET} ")
if _have("zoxide"):
    execx($(zoxide init xonsh), "exec", __xonsh__.ctx, filename="zoxide")

@events.on_ptk_create
def _ember_keys(bindings, **kw):
    import subprocess
    if not _have("fzf"):
        return  # keep xonsh's built-in ctrl-r search

    def _fzf(event, lines, *opts):
        try:
            r = subprocess.run(["fzf", "--height=45%", *opts], input="\n".join(lines), text=True, stdout=subprocess.PIPE)
        finally:
            event.cli.renderer.erase()
        return r.stdout.rstrip("\n")

    @bindings.add("c-r")
    def _history(event):
        seen, items = set(), []
        for item in __xonsh__.history.all_items(newest_first=True):
            cmd = item["inp"].rstrip()
            if cmd and cmd not in seen:
                seen.add(cmd)
                items.append(cmd.replace("\n", " ⏎ "))
            if len(items) >= 5000:
                break
        pick = _fzf(event, items, "--scheme=history", "--no-sort", "--input-label= history ", "--query", event.current_buffer.text)
        if pick:
            event.current_buffer.text = pick.replace(" ⏎ ", "\n")
            event.current_buffer.cursor_position = len(event.current_buffer.text)

    @bindings.add("c-t")
    def _files(event):
        lister = ["rg", "--files", "--hidden", "-g", "!.git"] if _have("rg") else ["find", ".", "-type", "f", "-not", "-path", "./.git/*"]
        out = subprocess.run(lister, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
        preview = ["--preview", "bat --color=always --style=numbers --line-range=:200 {}"] if _have("bat") else []
        pick = _fzf(event, out.splitlines(), "--input-label= files ", *preview)
        if pick:
            event.current_buffer.insert_text(pick)

# conda is loaded on first use (its hook costs ~200 ms at startup). anaconda3/bin is
# usually already on PATH (see local.xsh), so base python works without it; `conda activate <env>` works after.
def _conda_lazy(args):
    del aliases["conda"]
    src = $(@(_conda_exe) shell.xonsh hook)
    src = "\n".join(l for l in src.splitlines() if not l.startswith("conda activate"))
    execx(src, "exec", __xonsh__.ctx, filename="conda-hook")
    # xonsh will not re-enter an alias by name from inside itself, so call the hook's entry point
    return __xonsh__.ctx["_conda_main"](args)

_conda_exe = next((str(p) for p in (_home / "anaconda3/bin/conda", _home / "miniconda3/bin/conda", _home / "miniforge3/bin/conda") if p.exists()), None)
if _conda_exe:
    aliases["conda"] = _conda_lazy

# OSC 133 prompt marks (jump-to-prompt, command-finish notifications in Ghostty)
xontrib load -s term_integration

# --- the boot card: the first window of a login session (not in herdr panes, not in nested
#     shells). After that windows open straight to the prompt; `boot` shows it again.
def _ember_first_window():
    run = ${...}.get("XDG_RUNTIME_DIR")
    if not run:
        return True   # nowhere to remember: fall back to once per window
    try:
        os.close(os.open(os.path.join(run, "ember-booted"), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError:
        return False
    except OSError:
        return True
    return True

if $XONSH_INTERACTIVE and not ${...}.get("HERDR_PANE_ID") and not ${...}.get("EMBER_BOOTED") and sys.stdout.isatty() and os.get_terminal_size().columns >= 100:
    $EMBER_BOOTED = "1"
    if _have("fastfetch") and _ember_first_window():
        fastfetch
