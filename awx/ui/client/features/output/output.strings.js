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
        CANCEL: t.s('Cancel'),
        COLLAPSE_OUTPUT: t.s('Collapse Output'),
        DELETE: t.s('Delete'),
        DOWNLOAD_OUTPUT: t.s('Download Output'),
        CREDENTIAL: t.s('View the Credential'),
        EXPAND_OUTPUT: t.s('Expand Output'),
        EXTRA_VARS: t.s('Read-only view of extra variables added to the job template.'),
        INVENTORY: t.s('View the Inventory'),
        JOB_TEMPLATE: t.s('View the Job Template'),
        PROJECT: t.s('View the Project'),
        PROJECT_UPDATE: t.s('View Project checkout results'),
        SCHEDULE: t.s('View the Schedule'),
        SOURCE_WORKFLOW_JOB: t.s('View the source Workflow Job'),
        USER: t.s('View the User'),
    };

    ns.details = {
        HEADER: t.s('Details'),
        ISOLATED: t.s('Isolated'),
        NOT_FINISHED: t.s('Not Finished'),
        NOT_STARTED: t.s('Not Started'),
        SHOW_LESS: t.s('Show Less'),
        SHOW_MORE: t.s('Show More'),
    };

    ns.labels = {
        CREDENTIAL: t.s('Credential'),
        EXTRA_VARS: t.s('Extra Variables'),
        FINISHED: t.s('Finished'),
        FORKS: t.s('Forks'),
        INSTANCE_GROUP: t.s('Instance Group'),
        INVENTORY: t.s('Inventory'),
        JOB_EXPLANATION: t.s('Explanation'),
        JOB_TAGS: t.s('Job Tags'),
        JOB_TEMPLATE: t.s('Job Template'),
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
        PLAYBOOK: t.s('Playbook'),
        PROJECT: t.s('Project'),
        RESULT_TRACEBACK: t.s('Error Details'),
        SCM_REVISION: t.s('Revision'),
        SKIP_TAGS: t.s('Skip Tags'),
        SOURCE: t.s('Source'),
        SOURCE_CREDENTIAL: t.s('Source Credential'),
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
    };

    ns.stdout = {
        BACK_TO_TOP: t.s('Back to Top'),
    };
}

OutputStrings.$inject = ['BaseStringService'];

export default OutputStrings;
