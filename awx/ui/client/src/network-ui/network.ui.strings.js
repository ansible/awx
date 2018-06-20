function awxNetStrings (BaseString) {
    BaseString.call(this, 'awxNet');

    const { t } = this;
    const ns = this.awxNet;

    ns.feature = {
        ACTION_BUTTON: t.s('Network Visualizer')
    };

    ns.state = {
        BREADCRUMB_LABEL: t.s('NETWORK VISUALIZER')
    };

    ns.toolbox = {
        INVENTORY: t.s('Inventory')
    };

    ns.actions = {
        ACTIONS: t.s('ACTIONS'),
        EXPORT: t.s('Export'),
        EXPAND_PANEL: t.s('Expand Panel'),
        COLLAPSE_PANEL: t.s('Collapse Panel')
    };

    ns.key = {
        KEY: t.s('Key'),
        DEBUG_MODE: t.s('Debug Mode'),
        HIDE_CURSOR: t.s('Hide Cursor'),
        HIDE_BUTTONS: t.s('Hide Buttons'),
        HIDE_INTERFACES: t.s('Hide Interfaces'),
        RESET_ZOOM: t.s('Reset Zoom')
    };

    ns.search = {
        SEARCH: t.s('SEARCH'),
        HOST: t.s('Host'),
        SWITCH: t.s('Switch'),
        ROUTER: t.s('Router'),
        UNKNOWN: t.s('Unknown')
    };

    ns.context_menu = {
        DETAILS:  t.s('Details'),
        REMOVE: t.s('Remove')
    };

    ns.details = {
        HOST_NAME: t.s('Host Name'),
        DESCRIPTION: t.s('Description'),
        HOST_POPOVER: t.s('Provide a host name, ip address, or ip address:port. Examples include:'),
        SAVE_COMPLETE: t.s('Save Complete'),
        CLOSE: t.s('Close')
    };

}

awxNetStrings.$inject = ['BaseStringService'];

export default awxNetStrings;
