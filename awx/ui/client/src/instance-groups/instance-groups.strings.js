function InstanceGroupsStrings (BaseString) {
    BaseString.call(this, 'instanceGroups');

    const { t } = this;
    const ns = this.instanceGroups;

    ns.state = {
        INSTANCE_GROUPS_BREADCRUMB_LABEL: t.s('INSTANCE GROUPS'),
        INSTANCES_BREADCRUMB_LABEL: t.s('INSTANCES'),
        ADD_BREADCRUMB_LABEL: t.s('CREATE INSTANCE GROUP'),
        EDIT_BREADCRUMB_LABEL: t.s('EDIT INSTANCE GROUP')
    };

    ns.list = {
        MANUAL: t.s('MANUAL'),
        PANEL_TITLE: t.s('INSTANCE GROUPS'),
        ROW_ITEM_LABEL_INSTANCES: t.s('Instances'),
        ROW_ITEM_LABEL_RUNNING_JOBS: t.s('Running Jobs'),
        ROW_ITEM_LABEL_TOTAL_JOBS: t.s('Total Jobs'),
        ROW_ITEM_LABEL_USED_CAPACITY: t.s('Used Capacity')
    };

    ns.tab = {
        DETAILS: t.s('DETAILS'),
        INSTANCES: t.s('INSTANCES'),
        JOBS: t.s('JOBS')
    };

    ns.tooltips = {
        ADD_INSTANCE_GROUP: t.s('Create a new Instance Group'),
        ASSOCIATE_INSTANCES: t.s('Associate an existing Instance'),
        DOCS_HELP_TEXT: t.s('Instance Groups Help')
    };

    ns.instance = {
        PANEL_TITLE: t.s('SELECT INSTANCE')
    };

    ns.capacityBar = {
        IS_OFFLINE: t.s('Unavailable to run jobs.'),
        IS_OFFLINE_LABEL: t.s('Unavailable'),
        USED_CAPACITY: t.s('Used Capacity')
    };

    ns.capacityAdjuster = {
        CPU: t.s('CPU'),
        RAM: t.s('RAM'),
        FORKS: t.s('Forks')
    };

    ns.jobs = {
        PANEL_TITLE: t.s('Jobs'),
        RUNNING_JOBS: t.s('Running Jobs')
    };

    ns.error = {
        HEADER: this.error.HEADER,
        CALL: this.error.CALL,
        DELETE: t.s('Unable to delete instance group.'),
    };

    ns.alert  = {
        MISSING_PARAMETER: t.s('Instance Group parameter is missing.'),
    };

    ns.sort = {
        NAME_ASCENDING: t.s('Name (Ascending)'),
        NAME_DESCENDING: t.s('Name (Descending)')
    };
}

InstanceGroupsStrings.$inject = ['BaseStringService'];

export default InstanceGroupsStrings;
