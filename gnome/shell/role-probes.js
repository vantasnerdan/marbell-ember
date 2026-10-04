// Run only inside preview.py's private Shell; exercise the actual St CSS cascade.
(async () => {
    const {default: St} = await import('gi://St');
    const root = new St.BoxLayout({style_class: 'modal-dialog', vertical: true,
        style: 'spacing: 10px; padding: 24px; width: 500px;'});
    Main.layoutManager.addChrome(root);
    root.set_position(450, 120);
    const checks = [];
    function rgb(c) { return '#' + [c.red, c.green, c.blue].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase(); }
    function actor(cls, pseudo = '', parent = root, type = St.Button) {
        const a = new type({style_class: cls});
        parent.add_child(a);
        for (const p of pseudo.split(' ').filter(Boolean)) a.add_style_pseudo_class(p);
        return a;
    }
    function check(name, a, property, expected) {
        const node = a.get_theme_node();
        const value = property === 'foreground' ? node.get_foreground_color()
            : property === 'background' ? node.get_background_color()
            : property === 'border' ? node.get_border_color(St.Side.TOP)
            : property === 'ring' ? node.get_box_shadow().color
            : node.get_color(property);
        const actual = rgb(value);
        checks.push({name, property, actual, expected, pass: actual === expected, ...(actual !== expected ? {cssClass:a.get_style_class_name(), inline:a.get_style()} : {})});
    }
    const title = actor('dialog-title', '', root, St.Label);
    title.text = 'Ember state and colour checks';
    check('dialog title', title, 'foreground', '#F4F7FB');
    const entry = actor('search-entry', 'focus', root, St.Entry);
    entry.set_text('Focused field / selected text');
    check('entry selection', entry, 'selection-background-color', '#26365A');
    check('entry cursor', entry, 'caret-color', '#F47853');
    check('entry focus ring', entry, 'ring', '#F47853');
    entry.set_hint_text('Search');
    const hint = entry.get_hint_actor();
    check('entry hint', hint, 'foreground', '#5B6B8C');
    const quick = actor('quick-settings popup-menu-content', '', root, St.BoxLayout);
    const toggle = actor('quick-toggle button', 'checked', quick);
    toggle.label = 'Enabled';
    check('checked quick tile', toggle, 'background', '#26365A');
    check('checked quick title', toggle, 'foreground', '#F47853');
    const off = actor('quick-toggle button', '', quick);
    const offIcon = actor('quick-toggle-icon', '', off, St.Icon);
    check('inactive quick icon', offIcon, 'foreground', '#5B6B8C');
    const sub = actor('quick-toggle-subtitle', '', off, St.Label);
    check('secondary quick text', sub, 'foreground', '#5B6B8C');
    const switch_ = actor('toggle-switch', 'checked');
    check('switch on', switch_, 'background', '#F47853');
    const box = actor('check-box', 'checked');
    const icon = actor('', '', box, St.Icon);
    check('checkbox on', icon, 'background', '#F47853');
    check('checkbox mark', icon, 'foreground', '#070B16');
    const slider = actor('slider');
    check('slider track', slider, '-barlevel-background-color', '#1E2A44');
    check('slider fill', slider, '-barlevel-active-background-color', '#F47853');
    check('slider overdrive', slider, '-barlevel-overdrive-color', '#E5484D');
    const selected = actor('popup-menu-item', 'selected');
    selected.label = 'Selected menu row';
    check('selected menu row', selected, 'background', '#26365A');
    const switcher = actor('switcher-list', '', root, St.BoxLayout);
    const item = actor('item-box', 'selected', switcher);
    item.label = 'Selected window';
    check('switcher selection', item, 'background', '#26365A');
    check('switcher marker', item, 'foreground', '#F47853');
    const calendar = actor('calendar', '', root, St.BoxLayout);
    const today = actor('calendar-day calendar-today', '', calendar);
    today.label = '04';
    check('today', today, 'background', '#F47853');
    check('today text', today, 'foreground', '#070B16');
    const selectedDay = actor('calendar-day', 'selected', calendar);
    selectedDay.label = '05';
    check('selected day', selectedDay, 'background', '#26365A');
    const buttons = actor('modal-dialog-button-box', '', root, St.BoxLayout);
    const primary = actor('modal-dialog-button', 'default', buttons);
    primary.label = 'Continue';
    check('suggested action', primary, 'background', '#F47853');
    check('suggested text', primary, 'foreground', '#070B16');
    const close = actor('window-close', 'hover');
    check('close hover', close, 'background', '#F47853');
    const prompt = actor('prompt-dialog', '', root, St.BoxLayout);
    for (const [name, cls, expected] of [['success', 'success', '#4FD1C5'],
        ['warning', 'warning', '#F2B866'], ['error', 'prompt-dialog-error-label', '#E5484D'],
        ['info', 'prompt-dialog-info-label', '#6E9BF5']]) {
        const label = actor(cls, '', prompt, St.Label);
        label.text = name;
        check(name, label, 'foreground', expected);
    }
    const link = actor('url-highlighter');
    check('link', link, 'link-color', '#6E9BF5');
    check('popup border', quick, 'border', '#1E2A44');
    primary.add_style_pseudo_class('hover');
    check('suggested hover', primary, 'background', '#FF9A7B');
    check('suggested hover text', primary, 'foreground', '#070B16');
    primary.add_style_pseudo_class('insensitive');
    check('suggested disabled', primary, 'foreground', '#5B6B8C');
    const apps = actor('apps-scroll-view', '', root, St.BoxLayout);
    const progress = actor('progress-bar', '', apps);
    check('progress fill', progress, '-progress-bar-background', '#F47853');
    check('progress track', progress, '-progress-bar-track-background', '#1E2A44');
    const panel = actor('', '', root, St.BoxLayout);
    panel.set_name('panel');
    const panelButton = actor('panel-button', 'checked', panel);
    check('panel active marker', panelButton, 'foreground', '#F47853');
    check('panel active fill', panelButton, 'ring', '#26365A');
    const destructive = actor('button destructive-action');
    check('destructive action', destructive, 'background', '#E5484D');
    const ornament = actor('popup-menu-ornament', '', selected, St.Label);
    check('menu check marker', ornament, 'foreground', '#F47853');
    toggle.add_style_pseudo_class('insensitive');
    check('checked disabled quick tile', toggle, 'foreground', '#5B6B8C');
    const monthHeader = actor('calendar-month-header', '', calendar, St.BoxLayout);
    const month = actor('calendar-month-label', '', monthHeader, St.Label);
    check('calendar heading', month, 'foreground', '#F4F7FB');
    const events = actor('events-button', '', root, St.BoxLayout);
    const eventsBox = actor('events-box', '', events, St.BoxLayout);
    const eventsList = actor('events-list', '', eventsBox, St.BoxLayout);
    const placeholder = actor('event-placeholder', '', eventsList, St.Label);
    check('event placeholder', placeholder, 'foreground', '#5B6B8C');
    const panelIcon = actor('system-status-icon', '', panelButton, St.Icon);
    check('panel active icon', panelIcon, 'foreground', '#F47853');
    const record = actor('panel-button screen-recording-indicator', 'checked', panel);
    const recordIcon = actor('system-status-icon', '', record, St.Icon);
    check('recording icon', recordIcon, 'foreground', '#070B16');
    root.destroy();
    return checks;
})()
