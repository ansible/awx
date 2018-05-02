function InstanceGroupsStrings (BaseString) {
    BaseString.call(this, 'instanceGroups');

    const { t } = this;
    const ns = this.instanceGroups;

    ns.state = {
        ADD_BREADCRUMB_LABEL: t.s('CREATE INSTANCE GROUP'),
        EDIT_BREADCRUMB_LABEL: t.s('EDIT INSTANCE GROUP')
    };

    ns.list = {
        PANEL_TITLE: t.s('INSTANCE GROUPS')
    };

    ns.tab = {
        DETAILS: t.s('DETAILS'),
        INSTANCES: t.s('INSTANCES'),
        JOBS: t.s('JOBS')
    };

    ns.tooltips = {
        ADD_INSTANCE_GROUP: t.s('Create a new Instance Group'),
        ASSOCIATE_INSTANCES: t.s('Associate an existing Instance')
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

    ns.error = {
        HEADER: this.error.HEADER,
        CALL: this.error.CALL,
        DELETE: t.s('Unable to delete instance group.'),
    };

    ns.alert  = {
        MISSING_PARAMETER: t.s('Instance Group parameter is missing.'),
    };

}

InstanceGroupsStrings.$inject = ['BaseStringService'];

export default InstanceGroupsStrings;
