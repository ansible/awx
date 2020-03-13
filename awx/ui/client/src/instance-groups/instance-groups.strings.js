function InstanceGroupsStrings(BaseString) {
    BaseString.call(this, 'instanceGroups');

    const {
        t
    } = this;
    const ns = this.instanceGroups;

    ns.state = {
        INSTANCE_GROUPS_BREADCRUMB_LABEL: t.s('INSTANCE GROUPS'),
        INSTANCES_BREADCRUMB_LABEL: t.s('INSTANCES'),
        ADD_BREADCRUMB_LABEL: t.s('CREATE INSTANCE GROUP'),
        ADD_CONTAINER_GROUP_BREADCRUMB_LABEL: t.s('CREATE CONTAINER GROUP'),
        TECH_PREVIEW_MESSAGE_BAR: t.s('This feature is currently in tech preview and is subject to change in a future release.  Click here for documentation.'),
    };

    ns.list = {
        MANUAL: t.s('MANUAL'),
        PANEL_TITLE: t.s('INSTANCE GROUPS'),
        ROW_ITEM_LABEL_INSTANCES: t.s('Instances'),
        ROW_ITEM_LABEL_ISOLATED: t.s('ISOLATED'),
        ROW_ITEM_LABEL_RUNNING_JOBS: t.s('Running Jobs'),
        ROW_ITEM_LABEL_TOTAL_JOBS: t.s('Total Jobs'),
        ROW_ITEM_LABEL_USED_CAPACITY: t.s('Used Capacity'),
        ADD: t.s('Add a new instance group')
    };

    ns.tab = {
        DETAILS: t.s('DETAILS'),
        INSTANCES: t.s('INSTANCES'),
        JOBS: t.s('JOBS')
    };

    ns.tooltips = {
        ADD_INSTANCE_GROUP: t.s('Create a new Instance Group'),
        ASSOCIATE_INSTANCES: t.s('Associate an existing Instance'),
        IG_DOCS_HELP_TEXT: t.s('Instance Groups Help'),
        CG_DOCS_HELP_TEXT: t.s('Container Groups Help')
    };

    ns.instance = {
        PANEL_TITLE: t.s('SELECT INSTANCE'),
        BADGE_TEXT: t.s('Instance Group'),
        ADD: t.s('Add a new instance')
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

    ns.alert = {
        MISSING_PARAMETER: t.s('Instance Group parameter is missing.'),
    };
    ns.container = {
        PANEL_TITLE: t.s('Add Container Group'),
        LOOK_UP_TITLE: t.s('Add Credential'),
        CREDENTIAL_PLACEHOLDER: t.s('SELECT A CREDENTIAL'),
        POD_SPEC_LABEL: t.s('Pod Spec Override'),
        BADGE_TEXT: t.s('Container Group'),
        POD_SPEC_TOGGLE: t.s('Customize Pod Spec'),
        CREDENTIAL_HELP_TEXT: t.s('Credential to authenticate with Kubernetes or OpenShift.  Must be of type \"Kubernetes/OpenShift API Bearer Token\”.'),
        EXTRA_VARS_HELP_TEXT: t.s('Field for passing a custom Kubernetes or OpenShift Pod specification.')
    };
}

InstanceGroupsStrings.$inject = ['BaseStringService'];

export default InstanceGroupsStrings;
