// St's actual libcroco parser, not GTK CSS or a browser parser.
const {Gio, St} = imports.gi;
const theme = new St.Theme();
theme.load_stylesheet(Gio.File.new_for_path(ARGV[0]));
print('PASS: St.Theme.load_stylesheet parsed ' + ARGV[0]);
