function JobsStrings (BaseString) {
    BaseString.call(this, 'jobs');

    const { t } = this;
    const ns = this.jobs;

    ns.list = {
        PANEL_TITLE: t.s('JOBS'),
        ROW_ITEM_LABEL_STARTED: t.s('Started'),
        ROW_ITEM_LABEL_FINISHED: t.s('Finished'),
        ROW_ITEM_LABEL_WORKFLOW_JOB: t.s('Workflow Job'),
        ROW_ITEM_LABEL_LAUNCHED_BY: t.s('Launched By'),
        ROW_ITEM_LABEL_JOB_TEMPLATE: t.s('Job Template'),
        ROW_ITEM_LABEL_INVENTORY: t.s('Inventory'),
        ROW_ITEM_LABEL_PROJECT: t.s('Project'),
        ROW_ITEM_LABEL_CREDENTIALS: t.s('Credentials'),
        ROW_ITEM_LABEL_WEBHOOK: t.s('Webhook'),
        NO_RUNNING: t.s('There are no running jobs.'),
        JOB: t.s('Job'),
        STATUS_TOOLTIP: status => t.s('Job {{status}}. Click for details.', { status }),
        SLICE_JOB: t.s('Slice Job'),
        NEW: t.s('new'),
        PENDING: t.s('pending'),
        WAITING: t.s('waiting'),
        RUNNING: t.s('running'),
        SUCCESSFUL: t.s('successful'),
        FAILED: t.s('failed'),
        ERROR: t.s('error'),
        CANCELED: t.s('canceled')
    };
}

JobsStrings.$inject = ['BaseStringService'];

export default JobsStrings;
