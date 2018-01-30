function JobStrings (BaseString) {
    BaseString.call(this, 'jobs');

    const { t } = this;
    const ns = this.jobs;

    ns.state = {
        LIST_BREADCRUMB_LABEL: t.s('JOBS')
    };

    ns.list = {
        PANEL_TITLE: t.s('JOBS'),
        ADD_BUTTON_LABEL: t.s('ADD'),
        ADD_DD_JT_LABEL: t.s('Job Template'),
        ADD_DD_WF_LABEL: t.s('Workflow Template'),
        ROW_ITEM_LABEL_ACTIVITY: t.s('Activity'),
        ROW_ITEM_LABEL_INVENTORY: t.s('Inventory'),
        ROW_ITEM_LABEL_PROJECT: t.s('Project'),
        ROW_ITEM_LABEL_TEMPLATE: t.s('Template'),
        ROW_ITEM_LABEL_CREDENTIALS: t.s('Credentials'),
        ROW_ITEM_LABEL_MODIFIED: t.s('Last Modified'),
        ROW_ITEM_LABEL_RAN: t.s('Last Ran'),
        ROW_ITEM_LABEL_STARTED: t.s('Started'),
        ROW_ITEM_LABEL_FINISHED: t.s('Finished')
    };
}

JobStrings.$inject = ['BaseStringService'];

export default JobStrings;
