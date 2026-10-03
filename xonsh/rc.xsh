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
$XONSH_PROMPT_CURSOR_SHAPE = "blinking-block"
$EMBER_CALLSIGN = ${...}.get("EMBER_CALLSIGN", "MARBELL")

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
    "Token.Punctuation": "#5B6B8C",
    "Token.Literal.String": "#F2B866",
    "Token.Literal.String.Escape": "#FFD08A",
    "Token.Literal.Number": "#FF9A7B",
    "Token.Comment": "italic #5B6B8C",
    "Token.Error": "#E5484D",
    "Token.PTK.AutoSuggestion": "#5B6B8C",
    "Token.PTK.Aborting": "#5B6B8C",
    "Token.PTK.CompletionMenu": "bg:#111829 #C9D3E3",
    "Token.PTK.CompletionMenu.Completion": "bg:#111829 #C9D3E3",
    "Token.PTK.CompletionMenu.Completion.Current": "bg:#F47853 #070B16 bold",
    "Token.PTK.CompletionMenu.Meta.Completion": "bg:#0C1220 #5B6B8C",
    "Token.PTK.CompletionMenu.Meta.Completion.Current": "bg:#1E2A44 #F4F7FB",
    "Token.PTK.Scrollbar.Background": "bg:#111829",
    "Token.PTK.Scrollbar.Button": "bg:#F47853",
    "Token.PTK.BottomToolbar": "noreverse bg:#0A0F1D #5B6B8C",
    "Token.PTK.MatchingBracket.Cursor": "bold #F47853",
    "Token.PTK.MatchingBracket.Other": "bold #4FD1C5",
})

# --- tool colours ------------------------------------------------------------------
$EZA_COLORS = ":".join([
    "di=1;38;2;157;184;255", "ex=38;2;79;209;197", "ln=38;2;92;200;240", "or=38;2;229;72;77",
    "ur=38;2;91;107;140", "uw=38;2;91;107;140", "ux=38;2;79;209;197", "ue=38;2;79;209;197",
    "gr=38;2;91;107;140", "gw=38;2;91;107;140", "gx=38;2;91;107;140",
    "tr=38;2;91;107;140", "tw=38;2;242;184;102", "tx=38;2;91;107;140",
    "sn=38;2;244;120;83", "sb=38;2;91;107;140", "nb=38;2;91;107;140", "nk=38;2;201;211;227",
    "nm=38;2;242;184;102", "ng=38;2;244;120;83", "nt=38;2;229;72;77",
    "uu=38;2;91;107;140", "un=38;2;242;184;102", "gu=38;2;91;107;140", "da=38;2;91;107;140",
    "ga=38;2;79;209;197", "gm=38;2;242;184;102", "gd=38;2;229;72;77", "gv=38;2;92;200;240", "gt=38;2;244;120;83",
    "xx=38;2;30;42;68", "hd=4;38;2;91;107;140", "lp=38;2;92;200;240",
    "*.md=38;2;244;247;251", "*.json=38;2;242;184;102", "*.toml=38;2;242;184;102", "*.py=38;2;255;154;123",
])
$FZF_DEFAULT_OPTS = " ".join([
    "--style=full", "--layout=reverse", "--height=60%", "--border=rounded", "--info=inline-right",
    "--prompt='❯ '", "--pointer='▌'", "--marker='●'", "--highlight-line",
    "--color=bg:-1,bg+:#111829,fg:#C9D3E3,fg+:#F4F7FB,hl:#F47853,hl+:#FF9A7B,gutter:-1",
    "--color=info:#5B6B8C,prompt:#F47853,pointer:#F47853,marker:#4FD1C5,spinner:#F2B866",
    "--color=header:#5B6B8C,border:#1E2A44,label:#5B6B8C,query:#F4F7FB,separator:#1E2A44,scrollbar:#F47853",
    "--color=list-border:#1E2A44,input-border:#F47853,preview-border:#1E2A44,header-border:#1E2A44",
])
$BAT_THEME = "ansi"
$MANPAGER = "sh -c 'col -bx | bat -l man -p'"
$MANROFFOPT = "-c"

# --- aliases ------------------------------------------------------------------------
aliases["ls"] = "eza --icons=auto --group-directories-first"
aliases["ll"] = "eza --icons=auto --group-directories-first -l --git --time-style=relative --no-user"
aliases["la"] = "eza --icons=auto --group-directories-first -la --git --time-style=relative"
aliases["lt"] = "eza --icons=auto --group-directories-first --tree --level=2"
aliases["cat"] = "bat --paging=never"
aliases["top"] = "btop"
aliases["boot"] = "fastfetch"
aliases["grep"] = "grep --color=auto"

# --- ember: Python graphics at the prompt (spark, bars, gauge, panel, table) -------------
sys.path.insert(0, str(_home / ".config/ember"))
import ember
from ember import spark, bars, gauge, panel, table

def _ember_toolbar():
    try:
        text = __xonsh__.shell.shell.prompter.default_buffer.text
    except Exception:
        text = ""
    def _is_cmd(word):
        return word in aliases or bool(__xonsh__.commands_cache.locate_binary(word))
    try:
        return ember.toolbar(text, _is_cmd)
    except Exception:
        return ""

$BOTTOM_TOOLBAR = _ember_toolbar

# --- prompt, jumps, history search -----------------------------------------------------
execx($(starship init xonsh))
$RIGHT_PROMPT = ""

# The status line has to repaint on every key (for the SHELL / PYTHON flag), which makes
# xonsh re-evaluate $PROMPT on every key too. Starship is a subprocess, so run it once
# per prompt and hand back the cached string after that.
_starship_prompt = $PROMPT
_prompt_cache = {}

@events.on_pre_prompt
def _ember_new_prompt(**kw):
    _prompt_cache.clear()

def _ember_prompt():
    if "p" not in _prompt_cache:
        _prompt_cache["p"] = _starship_prompt()
    return _prompt_cache["p"]

$PROMPT = _ember_prompt
$UPDATE_PROMPT_ON_KEYPRESS = True
execx($(zoxide init xonsh), "exec", __xonsh__.ctx, filename="zoxide")

@events.on_ptk_create
def _ember_keys(bindings, **kw):
    import subprocess

    def _fzf(event, lines, *opts):
        try:
            r = subprocess.run(["fzf", "--height=45%", *opts], input="\n".join(lines), text=True, stdout=subprocess.PIPE)
        finally:
            event.cli.renderer.erase()
        return r.stdout.rstrip("\n")

    @bindings.add("c-r")
    def _history(event):
        seen, items = set(), []
        for item in reversed(list(__xonsh__.history.all_items())):
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
        out = subprocess.run(["rg", "--files", "--hidden", "-g", "!.git"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
        pick = _fzf(event, out.splitlines(), "--input-label= files ", "--preview", "bat --color=always --style=numbers --line-range=:200 {}")
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

# --- first shell in a window: the boot card (not in herdr panes, not in nested shells) -----
if $XONSH_INTERACTIVE and not ${...}.get("HERDR_PANE_ID") and not ${...}.get("EMBER_BOOTED") and sys.stdout.isatty() and os.get_terminal_size().columns >= 100:
    $EMBER_BOOTED = "1"
    fastfetch
