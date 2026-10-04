#!/usr/bin/python3
"""Render a finite smoke test in a PRIVATE headless Shell, never the live session.
Uses only the official installed User Themes extension. Needs system GI and GNOME 50.
Temporary bus, runtime, settings, apps and Shell are shut down on exit.
"""
import argparse
import json
import os
import signal
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from gi.repository import Gio, GLib

UUID='user-theme@gnome-shell-extensions.gcampax.github.com'


def main(output, icons=None):
    output.mkdir(parents=True,exist_ok=True)
    data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
    with tempfile.TemporaryDirectory(prefix='marbell-preview-') as directory:
        root=Path(directory)
        for name in ('config','data','cache','runtime','folders'):(root/name).mkdir(mode=0o700)
        for name in ('Desktop','Documents','Downloads','Music','Pictures','Projects','Videos'):(root/'folders'/name).mkdir()
        config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
        for version in ('gtk-3.0','gtk-4.0'):
            css=config/version/'gtk.css'
            if css.is_file():
                (root/'config'/version).mkdir()
                shutil.copy2(css,root/'config'/version/'gtk.css')
        (root/'config/user-dirs.dirs').write_text(''.join(
            f'XDG_{key}_DIR="{root / "folders" / folder}"\n'
            for key,folder in [('DESKTOP','Desktop'),('DOCUMENTS','Documents'),('DOWNLOAD','Downloads'),
                               ('MUSIC','Music'),('PICTURES','Pictures'),('VIDEOS','Videos')]))
        for group in ('themes','icons','fonts'):
            if group=='icons' and icons:
                (root/'data/icons').mkdir()
                (root/'data/icons/Marbell-Ember').symlink_to(icons,target_is_directory=True)
                continue
            if (data/group).exists():(root/'data'/group).symlink_to(data/group,target_is_directory=True)
        extensions=root/'data/gnome-shell/extensions'
        extensions.mkdir(parents=True)
        (extensions/UUID).symlink_to(data/'gnome-shell/extensions'/UUID,target_is_directory=True)
        env={**os.environ, 'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),
             'XDG_CACHE_HOME':str(root/'cache'),'XDG_RUNTIME_DIR':str(root/'runtime'),
             'GSETTINGS_BACKEND':'keyfile','GSK_RENDERER':'cairo','LIBGL_ALWAYS_SOFTWARE':'1',
             'GNOME_SHELL_SESSION_MODE':'user','XDG_CURRENT_DESKTOP':'GNOME',
             'GSETTINGS_SCHEMA_DIR':str(data/'gnome-shell/extensions'/UUID/'schemas')}
        for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','GNOME_KEYRING_CONTROL'):env.pop(key,None)
        def setting(schema,key,value):
            subprocess.run(['/usr/bin/gsettings','set',schema,key,value],env=env,check=True)
        setting('org.gnome.shell','enabled-extensions',str([UUID]))
        setting('org.gnome.shell','disable-user-extensions','false')
        setting('org.gnome.shell.extensions.user-theme','name','Marbell-Ember')
        setting('org.gnome.desktop.interface','icon-theme','Marbell-Ember')
        setting('org.gnome.desktop.interface','color-scheme','prefer-dark')
        setting('org.gnome.desktop.interface','gtk-theme',Gio.Settings.new('org.gnome.desktop.interface').get_string('gtk-theme'))
        setting('org.gnome.nautilus.preferences','default-folder-viewer','list-view')
        setting('org.gnome.nautilus.list-view','default-zoom-level','small')
        setting('org.gnome.desktop.interface','font-name',Gio.Settings.new('org.gnome.desktop.interface').get_string('font-name'))
        # Only the isolated test's backdrop; no private desktop data in screenshots.
        setting('org.gnome.desktop.background','picture-uri',"''")
        setting('org.gnome.desktop.background','picture-uri-dark',"''")
        setting('org.gnome.desktop.background','primary-color','#070B16')
        launch='printf "%s" "$DBUS_SESSION_BUS_ADDRESS" > "$1"; exec /usr/bin/gnome-shell --headless --wayland --no-x11 --virtual-monitor=1440x1000 --mode=user'
        log=(output/'headless-shell.log').open('w')
        process=subprocess.Popen(['/usr/bin/dbus-run-session','--','/bin/sh','-c',launch,'preview',str(root/'bus')],env=env,stdout=log,stderr=log,start_new_session=True)
        address=None
        try:
            deadline=time.monotonic()+25
            while not (root/'bus').exists():
                if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Headless Shell did not start')
                time.sleep(.1)
            address=(root/'bus').read_text()
            bus=Gio.DBusConnection.new_for_address_sync(address,Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT|Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,None,None)
            def call(dest,path,iface,method,args=None):
                return bus.call_sync(dest,path,iface,method,args,None,0,10000,None).unpack()
            while True:
                try:
                    call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',GLib.Variant('(s)',('org.gnome.Shell',)))
                    break
                except GLib.Error:
                    if time.monotonic()>deadline:raise
                    time.sleep(.1)
            time.sleep(3)
            # Explicit virtual input into THIS bus's headless session opens Looking Glass.
            remote='org.gnome.Mutter.RemoteDesktop'
            path=call(remote,'/org/gnome/Mutter/RemoteDesktop',remote,'CreateSession')[0]
            iface=remote+'.Session'
            call(remote,path,iface,'Start')
            def key(code,state):call(remote,path,iface,'NotifyKeyboardKeysym',GLib.Variant('(ub)',(code,state)))
            def tap(code):
                key(code,True);time.sleep(.03);key(code,False);time.sleep(.03)
            key(0xffe9,True);tap(0xffbf);key(0xffe9,False);time.sleep(.7)
            for c in 'lg':tap(ord(c))
            tap(0xff0d);time.sleep(.7)
            for c in 'global.context.unsafe_mode = true':tap(ord(c))
            tap(0xff0d);time.sleep(.3)
            call(remote,path,iface,'Stop')
            def evaluate(code):
                ok,result=call('org.gnome.Shell','/org/gnome/Shell','org.gnome.Shell','Eval',GLib.Variant('(s)',(code,)))
                if not ok:raise RuntimeError(f'Private Shell evaluation failed: {result}')
                return json.loads(result) if result else None
            def screenshot(name,delay=.6):
                time.sleep(delay)
                call('org.gnome.Shell','/org/gnome/Shell/Screenshot','org.gnome.Shell.Screenshot','Screenshot',GLib.Variant('(bbs)',(False,False,str(output/(name+'.png')))))
            report={'mode':'headless Wayland, independent D-Bus/runtime/keyfile settings',
                    'theme':evaluate('Main.getThemeStylesheet()?.get_path()'),
                    'font':evaluate('Main.panel.get_theme_node().get_font().to_string()'),
                    'extension':evaluate(f'Main.extensionManager.lookup({json.dumps(UUID)})?.state'),
                    'screenshots':[]}
            assert str(data/'themes/Marbell-Ember/gnome-shell/gnome-shell.css') in str(report['theme']) or 'Marbell-Ember' in str(report['theme']), report
            evaluate('Main.lookingGlass.close(); Main.overview.hide(); true')
            probes = Path(__file__).with_name('role-probes.js')
            if probes.exists():
                report['role_checks'] = evaluate(probes.read_text())
                failures = [x for x in report['role_checks'] if not x['pass']]
                if failures:
                    (output/'role-failures.json').write_text(json.dumps(failures, indent=2)+'\n')
                    raise RuntimeError(f'St colour-role checks failed: {failures}')
            time.sleep(.8)
            for name,code in [
                ('quick-settings','Main.panel.statusArea.quickSettings.menu.open(); true'),
                ('calendar','Main.panel.statusArea.quickSettings.menu.close(); Main.panel.statusArea.dateMenu.menu.open(); true'),
                ('overview','Main.panel.statusArea.dateMenu.menu.close(); Main.overview.show(); true'),
                ('app-grid','Main.overview.showApps(); true'),
                ('search','Main.overview.searchEntry.set_text("Files"); true'),
                ('screenshot-ui','Main.overview.searchEntry.set_text(""); Main.overview.hide(); true'),
            ]:
                if name == 'app-grid':
                    evaluate('Main.overview.hide(); true');time.sleep(.8)
                evaluate(code)
                if name == 'screenshot-ui':
                    time.sleep(.8);evaluate('Main.screenshotUI.open(); true')
                screenshot(name, 1.2 if name == 'search' else .6);report['screenshots'].append(name)
            evaluate('Main.screenshotUI.close(); true')
            evaluate('(async () => { const {default: Gio} = await import("gi://Gio"); Main.osdWindowManager.showOne(0, Gio.icon_new_for_string("audio-volume-high-symbolic"), "Volume", 0.55, 1); return true; })()')
            screenshot('osd',.3);report['screenshots'].append('osd')
            evaluate('(async () => { const {default: Gio} = await import("gi://Gio"); new Gio.Settings({schema_id:"org.gnome.desktop.a11y.applications"}).set_boolean("screen-keyboard-enabled", true); return true; })()')
            time.sleep(.4)
            evaluate('Main.keyboard.open(0); true');screenshot('keyboard');report['screenshots'].append('keyboard')
            evaluate('Main.keyboard.close(); true')
            time.sleep(1.5)
            evaluate('(async () => { const M = await import("resource:///org/gnome/shell/ui/messageTray.js"); const source = M.getSystemSource(); source.addNotification(new M.Notification({source, title:"Marbell Ember", body:"Notification preview: https://example.com"})); Main.panel.statusArea.dateMenu.menu.open(); return true; })()')
            screenshot('notification');report['screenshots'].append('notification')
            evaluate('Main.panel.statusArea.dateMenu.menu.close(); true')
            evaluate('(async () => { const M = await import("resource:///org/gnome/shell/ui/modalDialog.js"); const {default: St} = await import("gi://St"); global.emberPreviewDialog = new M.ModalDialog(); global.emberPreviewDialog.contentLayout.add_child(new St.Label({text:"Marbell Ember dialog preview", style_class:"dialog-title"})); const statuses = new St.BoxLayout({vertical:true, style_class:"prompt-dialog"}); for (const [text, style_class] of [["Ready / success","success"],["Attention / warning","warning"],["Failed / error","prompt-dialog-error-label"],["Information / link","prompt-dialog-info-label"]]) statuses.add_child(new St.Label({text, style_class})); global.emberPreviewDialog.contentLayout.add_child(statuses); global.emberPreviewDialog.setButtons([{label:"Cancel", action:() => {}}, {label:"Continue", default:true, action:() => {}}]); global.emberPreviewDialog.open(); return true; })()')
            screenshot('dialog');report['screenshots'].append('dialog')
            evaluate('global.emberPreviewDialog.close(); global.emberPreviewDialog.destroy(); true')
            private_env={**env,'DBUS_SESSION_BUS_ADDRESS':address,'WAYLAND_DISPLAY':'wayland-0'}
            nautilus=subprocess.Popen(['/usr/bin/nautilus','--new-window',str(root/'folders')],env=private_env,stdout=log,stderr=log)
            time.sleep(3);screenshot('nautilus-list');report['screenshots'].append('nautilus-list')
            (output/'preview-report.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({k:v for k,v in report.items() if k != 'role_checks'},indent=2),flush=True)
            print(f"PASS: {len(report.get('role_checks', []))} computed St colour-role checks",flush=True)
        finally:
            # Signal only this process group and bus's helper processes, never by executable name.
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            for proc in Path('/proc').glob('[0-9]*'):
                try:
                    entries=(proc/'environ').read_bytes().split(b'\0')
                    private=(f'XDG_RUNTIME_DIR={root / "runtime"}').encode() in entries
                    if private and int(proc.name)!=os.getpid():os.kill(int(proc.name),signal.SIGTERM)
                except (OSError,PermissionError):pass
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            log.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--icons',type=Path,help='Candidate Marbell-Ember directory; used only in the private session')
    args=parser.parse_args()
    main(args.output.resolve(),args.icons.resolve() if args.icons else None)
