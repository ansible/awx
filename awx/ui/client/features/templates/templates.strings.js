function TemplatesStrings (BaseString) {
    BaseString.call(this, 'templates');

    const { t } = this;
    const ns = this.templates;

    ns.state = {
        LIST_BREADCRUMB_LABEL: t.s('TEMPLATES')
    };

    ns.list = {
        PANEL_TITLE: t.s('TEMPLATES'),
        ADD_DD_JT_LABEL: t.s('Job Template'),
        ADD_DD_WF_LABEL: t.s('Workflow Template'),
        ROW_ITEM_LABEL_ACTIVITY: t.s('Activity'),
        ROW_ITEM_LABEL_INVENTORY: t.s('Inventory'),
        ROW_ITEM_LABEL_PROJECT: t.s('Project'),
        ROW_ITEM_LABEL_CREDENTIALS: t.s('Credentials'),
        ROW_ITEM_LABEL_MODIFIED: t.s('Last Modified'),
        ROW_ITEM_LABEL_RAN: t.s('Last Ran'),
    };

    ns.prompt = {
        INVENTORY: t.s('Inventory'),
        CREDENTIAL: t.s('Credential'),
        PROMPT: t.s('PROMPT'),
        OTHER_PROMPTS: t.s('Other Prompts'),
        SURVEY: t.s('Survey'),
        PREVIEW: t.s('Preview'),
        LAUNCH: t.s('LAUNCH'),
        CONFIRM: t.s('CONFIRM'),
        SELECTED: t.s('SELECTED'),
        NO_CREDENTIALS_SELECTED: t.s('No credentials selected'),
        NO_INVENTORY_SELECTED: t.s('No inventory selected'),
        REVERT: t.s('REVERT'),
        CREDENTIAL_TYPE: t.s('Credential Type'),
        CREDENTIAL_PASSWORD_WARNING: t.s('Credentials that require passwords on launch are not permitted for template schedules and workflow nodes.  The following credentials must be removed or replaced to proceed:'),
        PASSWORDS_REQUIRED_HELP: t.s('Launching this job requires the passwords listed below. Enter and confirm each password before continuing.'),
        PLEASE_ENTER_PASSWORD: t.s('Please enter a password.'),
        credential_passwords: {
            SSH_PASSWORD: t.s('SSH Password'),
            PRIVATE_KEY_PASSPHRASE: t.s('Private Key Passphrase'),
            PRIVILEGE_ESCALATION_PASSWORD: t.s('Privilege Escalation Password'),
            VAULT_PASSWORD: t.s('Vault Password')
        },
        SHOW_CHANGES: t.s('Show Changes'),
        SKIP_TAGS: t.s('Skip Tags'),
        JOB_TAGS: t.s('Job Tags'),
        LIMIT: t.s('Limit'),
        JOB_TYPE: t.s('Job Type'),
        VERBOSITY: t.s('Verbosity'),
        CHOOSE_JOB_TYPE: t.s('Choose a job type'),
        CHOOSE_VERBOSITY: t.s('Choose a verbosity'),
        EXTRA_VARIABLES: t.s('Extra Variables'),
        EXTRA_VARIABLES_HELP: t.s('<p>Pass extra command line variables to the playbook. This is the -e or --extra-vars command line parameter for ansible-playbook. Provide key/value pairs using either YAML or JSON.</p>JSON:<br /><blockquote>{<br />&quot;somevar&quot;: &quot;somevalue&quot;,<br />&quot;password&quot;: &quot;magic&quot;<br /> }</blockquote>YAML:<br /><blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>'),
        PLEASE_ENTER_ANSWER: t.s('Please enter an answer.'),
        PLEASE_SELECT_VALUE: t.s('Please select a value'),
        VALID_INTEGER: t.s('Please enter an answer that is a valid integer.'),
        VALID_DECIMAL: t.s('Please enter an answer that is a decimal number.'),
        PLAYBOOK_RUN: t.s('Playbook Run'),
        CHECK: t.s('Check'),
        NO_CREDS_MATCHING_TYPE: t.s('No Credentials Matching This Type Have Been Created'),
        CREDENTIAL_TYPE_MISSING: typeLabel => t.s('This job template has a default {{typeLabel}} credential which must be included or replaced before proceeding.', { typeLabel })
    };

    ns.alert  = {
        MISSING_PARAMETER: t.s('Template parameter is missing.'),
        NO_PERMISSION: t.s('You do not have permission to perform this action.'),
        UNKNOWN_COPY: t.s('Unable to determine this template\'s type while copying.'),
        UNKNOWN_DELETE: t.s('Unable to determine this template\'s type while deleting.'),
        UNKNOWN_EDIT: t.s('Unable to determine this template\'s type while editing.'),
        UNKNOWN_LAUNCH: t.s('Unable to determine this template\'s type while launching.'),
        UNKNOWN_SCHEDULE:  t.s('Unable to determine this template\'s type while scheduling.'),
    };

    ns.error = {
        HEADER: this.error.HEADER,
        CALL: this.error.CALL,
        EDIT: t.s('Unable to edit template.'),
        DELETE: t.s('Unable to delete template.'),
        LAUNCH: t.s('Unable to launch template.'),
        UNKNOWN: t.s('Unable to determine template type.'),
        SCHEDULE: t.s('Unable to schedule job.'),
        COPY: t.s('Unable to copy template.'),
        INVALID: t.s('Resources are missing from this template.')
    };

    ns.warnings = {
        WORKFLOW_RESTRICTED_COPY: t.s('You do not have access to all resources used by this workflow. Resources that you don\'t have access to will not be copied and will result in an incomplete workflow.')
    };

    ns.workflows = {
        INVALID_JOB_TEMPLATE: t.s('This Job Template is missing a default inventory or project. This must be addressed in the Job Template form before this node can be saved.'),
        CREDENTIAL_WITH_PASS: t.s('This Job Template has a credential that requires a password.  Credentials requiring passwords on launch are not permitted on workflow nodes.')
    };

    ns.workflow_maker = {
        DELETE_NODE_PROMPT_TEXT: t.s('Are you sure you want to delete this workflow node?'),
        KEY: t.s('KEY'),
        ON_SUCCESS: t.s('On Success'),
        ON_FAILURE: t.s('On Failure'),
        ALWAYS: t.s('Always'),
        PROJECT_SYNC: t.s('Project Sync'),
        INVENTORY_SYNC: t.s('Inventory Sync'),
        WARNING: t.s('Warning'),
        TOTAL_TEMPLATES: t.s('TOTAL TEMPLATES'),
        ADD_A_TEMPLATE: t.s('ADD A TEMPLATE'),
        EDIT_TEMPLATE: t.s('EDIT TEMPLATE'),
        JOBS: t.s('JOBS'),
        PLEASE_CLICK_THE_START_BUTTON: t.s('Please click the start button to build your workflow.'),
        PLEASE_HOVER_OVER_A_TEMPLATE: t.s('Please hover over a template for additional options.'),
        EDIT_LINK_TOOLTIP: t.s('Click to edit link'),
        VIEW_LINK_TOOLTIP: t.s('Click to view link'),
        RUN: t.s('RUN'),
        CHECK: t.s('CHECK'),
        SELECT: t.s('SELECT'),
        DELETED: t.s('DELETED'),
        START: t.s('START'),
        DETAILS: t.s('DETAILS'),
        TITLE: t.s('WORKFLOW VISUALIZER'),
        EDIT_LINK: ({ parentName, childName }) => t.s('EDIT LINK | {{parentName}} to {{childName}}', { parentName, childName }),
        VIEW_LINK: ({ parentName, childName }) => t.s('VIEW LINK | {{parentName}} to {{childName}}', { parentName, childName })
    }

}

TemplatesStrings.$inject = ['BaseStringService'];

export default TemplatesStrings;
