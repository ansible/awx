function InstanceGroupsStrings (BaseString) {
    BaseString.call(this, 'instanceGroups');

    const { t } = this;
    const ns = this.instanceGroups;

    ns.state = {
        ADD_BREADCRUMB_LABEL: t.s('CREATE INSTANCE GROUP'),
        EDIT_BREADCRUMB_LABEL: t.s('EDIT INSTANCE GROUP')
    };

    ns.tab = {
        DETAILS: t.s('DETAILS'),
        INSTANCES: t.s('INSTANCES'),
        JOBS: t.s('JOBS')
    };

    ns.instance = {
        PANEL_TITLE: t.s('SELECT INSTANCE')
    };

    ns.capacityBar = {
        IS_OFFLINE: t.s('Unavailable to run jobs.'),
        IS_OFFLINE_LABEL: t.s('Unavailable')
    };

    ns.jobs = {
        PANEL_TITLE: t.s('Jobs')
    };
}

InstanceGroupsStrings.$inject = ['BaseStringService'];

export default InstanceGroupsStrings;
