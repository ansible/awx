function OutputStrings (BaseString) {
    BaseString.call(this, 'output');

    const { t } = this;
    const ns = this.output;

    ns.state = {
        BREADCRUMB_DEFAULT: t.s('RESULTS'),
    };

    ns.status = {
        RUNNING: t.s('The host status bar will update when the job is complete.'),
        UNAVAILABLE: t.s('Host status information for this job is unavailable.'),
    };

    ns.tooltips = {
        ARTIFACTS: t.s('Read-only view of artifacts added to the job template'),
        CANCEL: t.s('Cancel'),
        COLLAPSE_OUTPUT: t.s('Collapse Output'),
        DELETE: t.s('Delete'),
        DOWNLOAD_OUTPUT: t.s('Download Output'),
        CREDENTIAL: t.s('View the Credential'),
        EXPAND_OUTPUT: t.s('Expand Output'),
        EXTRA_VARS: t.s('Read-only view of extra variables added to the job template'),
        HOST_LIMIT: t.s('When this field is true, the job\'s inventory belongs to an organization that has exceeded it\'s limit of hosts as defined by the system administrator.'),
        INVENTORY: t.s('View the Inventory'),
        INVENTORY_SCM: t.s('View the Project'),
        INVENTORY_SCM_JOB: t.s('View Project checkout results'),
        JOB_TEMPLATE: t.s('View the Job Template'),
        SLICE_JOB_DETAILS: t.s('Job is one of several from a JT that slices on inventory'),
        PROJECT: t.s('View the Project'),
        PROJECT_UPDATE: t.s('View Project checkout results'),
        SCHEDULE: t.s('View the Schedule'),
        SOURCE_WORKFLOW_JOB: t.s('View the source Workflow Job'),
        USER: t.s('View the User'),
        MENU_FIRST: t.s('Go to first page'),
        MENU_DOWN: t.s('Get next page'),
        MENU_UP: t.s('Get previous page'),
        MENU_LAST: t.s('Go to last page of available output'),
        MENU_FOLLOWING: t.s('Currently following output as it arrives. Click to unfollow'),
    };

    ns.details = {
        HEADER: t.s('Details'),
        ISOLATED: t.s('Isolated'),
        NOT_FINISHED: t.s('Not Finished'),
        NOT_STARTED: t.s('Not Started'),
        SHOW_LESS: t.s('Show Less'),
        SHOW_MORE: t.s('Show More'),
        UNKNOWN: t.s('Finished'),
    };

    ns.labels = {
        ARTIFACTS: t.s('Artifacts'),
        CREDENTIAL: t.s('Credential'),
        ENVIRONMENT: t.s('Environment'),
        EXECUTION_NODE: t.s('Execution Node'),
        EXTRA_VARS: t.s('Extra Variables'),
        FINISHED: t.s('Finished'),
        FORKS: t.s('Forks'),
        HOST_LIMIT_ERROR: t.s('Host Limit Error'),
        INSTANCE_GROUP: t.s('Instance Group'),
        INVENTORY: t.s('Inventory'),
        INVENTORY_SCM: t.s('Source Project'),
        JOB_EXPLANATION: t.s('Explanation'),
        JOB_TAGS: t.s('Job Tags'),
        JOB_TEMPLATE: t.s('Job Template'),
        SLICE_JOB: t.s('Slice Job'),
        JOB_TYPE: t.s('Job Type'),
        LABELS: t.s('Labels'),
        LAUNCHED_BY: t.s('Launched By'),
        LICENSE_ERROR: t.s('License Error'),
        LIMIT: t.s('Limit'),
        MACHINE_CREDENTIAL: t.s('Machine Credential'),
        MODULE_ARGS: t.s('Module Args'),
        NAME: t.s('Name'),
        OVERWRITE: t.s('Overwrite'),
        OVERWRITE_VARS: t.s('Overwrite Vars'),
        COMPATIBILITY_MODE: t.s('Compatibility Mode'),
        PLAYBOOK: t.s('Playbook'),
        PROJECT: t.s('Project'),
        RESULT_TRACEBACK: t.s('Error Details'),
        SCM_REVISION: t.s('Revision'),
        SKIP_TAGS: t.s('Skip Tags'),
        SOURCE: t.s('Source'),
        SOURCE_CREDENTIAL: t.s('Source Credential'),
        SOURCE_WORKFLOW_JOB: t.s('Source Workflow'),
        STARTED: t.s('Started'),
        STATUS: t.s('Status'),
        VERBOSITY: t.s('Verbosity'),
    };

    ns.search = {
        ADDITIONAL_INFORMATION_HEADER: t.s('ADDITIONAL_INFORMATION'),
        ADDITIONAL_INFORMATION: t.s('For additional information on advanced search syntax please see the Ansible Tower'),
        CLEAR_ALL: t.s('CLEAR ALL'),
        DOCUMENTATION: t.s('documentation'),
        EXAMPLES: t.s('EXAMPLES'),
        FIELDS: t.s('FIELDS'),
        KEY: t.s('KEY'),
        PLACEHOLDER_DEFAULT: t.s('SEARCH'),
        PLACEHOLDER_RUNNING: t.s('JOB IS STILL RUNNING'),
        REJECT_DEFAULT: t.s('Failed to update search results.'),
        REJECT_INVALID: t.s('Invalid search filter provided.'),
    };

    ns.stats = {
        ELAPSED: t.s('Elapsed'),
        PLAYS: t.s('Plays'),
        TASKS: t.s('Tasks'),
        HOSTS: t.s('Hosts')
    };

    ns.stdout = {
        BACK_TO_TOP: t.s('Back to Top'),
    };

    ns.host_event_modal = {
        CREATED: t.s('CREATED'),
        ID: t.s('ID'),
        PLAY: t.s('PLAY'),
        TASK: t.s('TASK'),
        MODULE: t.s('MODULE'),
        NO_RESULT_FOUND: t.s('No result found'),
        STANDARD_OUT: t.s('Standard Out'),
        STANDARD_ERROR: t.s('Standard Error')
    };

    ns.workflow_status = {
        SUCCESSFUL: t.s('SUCCESSFUL'),
        FAILED: t.s('FAILED'),
        NO_JOBS_FINISHED: t.s('NO JOBS FINISHED')
    };
}

OutputStrings.$inject = ['BaseStringService'];

export default OutputStrings;
