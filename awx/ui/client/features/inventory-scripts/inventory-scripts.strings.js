function InventoryScriptsStrings (BaseString) {
    BaseString.call(this, 'applications');

    const { t } = this;
    const ns = this.applications;

    ns.state = {
        TITLE: t.s('INVENTORY SCRIPTS'),
        LIST_BREADCRUMB_LABEL: t.s('INVENTORY SCRIPTS'),
        ADD_BREADCRUMB_LABEL: t.s('CREATE INVENTORY SCRIPT'),
        EDIT_BREADCRUMB_LABEL: t.s('EDIT INVENTORY SCRIPT')
    };

    ns.list = {
        ROW_ITEM_LABEL_ORGANIZATION: t.s('ORG'),
        ROW_ITEM_LABEL_MODIFIED: t.s('LAST MODIFIED'),
        DELETE_TOOLTIP: t.s('Delete Inventory Script'),
        COPY_TOOLTIP: t.s('Copy Inventory Script')
    };

    ns.add = {
        PANEL_TITLE: t.s('NEW INVENTORY SCRIPT')
    };
}

InventoryScriptsStrings.$inject = ['BaseStringService'];

export default InventoryScriptsStrings;
