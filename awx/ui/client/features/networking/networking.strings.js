function NetworkingStrings (BaseString) {
    BaseString.call(this, 'networking');

    const { t } = this;
    const ns = this.networking;

    ns.state = {
        BREADCRUMB_LABEL: t.s('INVENTORIES'),
    };

    ns.actions = {
        EXPAND_PANEL: t.s('Expand Panel'),
        COLLAPSE_PANEL: t.s('Collapse Panel')
    };
}

NetworkingStrings.$inject = ['BaseStringService'];

export default NetworkingStrings;
