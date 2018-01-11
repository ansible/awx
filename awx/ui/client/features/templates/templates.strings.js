function TemplatesStrings (BaseString) {
    BaseString.call(this, 'templates');

    const { t } = this;
    const ns = this.templates;

    ns.state = {
        LIST_BREADCRUMB_LABEL: t.s('TEMPLATES')
    }

    ns.list = {
        PANEL_TITLE: t.s('TEMPLATES'),
        ADD_BUTTON_LABEL: t.s('ADD'),
        ADD_DD_JT_LABEL: t.s('Job Template'),
        ADD_DD_WF_LABEL: t.s('Workflow Template'),
        ROW_ITEM_LABEL_ACTIVITY: t.s('Activity'),
        ROW_ITEM_LABEL_INVENTORY: t.s('Inventory'),
        ROW_ITEM_LABEL_PROJECT: t.s('Project'),
        ROW_ITEM_LABEL_CREDENTIALS: t.s('Credentials'),
        ROW_ITEM_LABEL_MODIFIED: t.s('Last Modified'),
        ROW_ITEM_LABEL_RAN: t.s('Last Ran'),
    }
}

TemplatesStrings.$inject = ['BaseStringService'];

export default TemplatesStrings;
