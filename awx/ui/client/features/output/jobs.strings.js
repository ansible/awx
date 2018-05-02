function JobsStrings (BaseString) {
    BaseString.call(this, 'jobs');

    const { t } = this;
    const ns = this.jobs;

    ns.state = {
        BREADCRUMB_DEFAULT: t.s('RESULTS'),
    };

    ns.status = {
        RUNNING: t.s('The host status bar will update when the job is complete.'),
        UNAVAILABLE: t.s('Host status information for this job is unavailable.'),
    };

    ns.resourceTooltips = {
        USER: t.s('View the User'),
        SCHEDULE: t.s('View the Schedule'),
        INVENTORY: t.s('View the Inventory'),
        CREDENTIAL: t.s('View the Credential'),
        JOB_TEMPLATE: t.s('View the Job Template'),
        SOURCE_WORKFLOW_JOB: t.s('View the source Workflow Job'),
        PROJECT: t.s('View the Project'),
        PROJECT_UPDATE: t.s('View Project checkout results')
    };

    ns.expandCollapse = {
        EXPAND: t.s('Expand Output'),
        COLLAPSE: t.s('Collapse Output')
    };
}

JobsStrings.$inject = ['BaseStringService'];

export default JobsStrings;
