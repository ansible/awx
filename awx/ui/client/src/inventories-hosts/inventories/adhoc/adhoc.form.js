/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Adhoc
 * @description This form is for executing an adhoc command
*/

export default ['i18n', function(i18n) {
    return {
        addTitle: i18n._('EXECUTE COMMAND'),
        name: 'adhoc',
        well: true,
        forceListeners: true,

        fields: {
            module_name: {
                label: i18n._('Module'),
                excludeModal: true,
                type: 'select',
                ngOptions: 'module.label for module in adhoc_module_options' +
                    ' track by module.value',
                ngChange: 'moduleChange()',
                required: true,
                awPopOver: i18n._('These are the modules that {{BRAND_NAME}} supports running commands against.'),
                dataTitle: i18n._('Module'),
                dataPlacement: 'right',
                dataContainer: 'body'
            },
            module_args: {
                label: 'Arguments',
                type: 'text',
                awPopOverWatch: 'argsPopOver',
                awPopOver: '{{ argsPopOver }}',
                dataTitle: i18n._('Arguments'),
                dataPlacement: 'right',
                dataContainer: 'body',
                autocomplete: false
            },
            limit: {
                label: i18n._('Limit'),
                type: 'text',

                awPopOver: '<p>The pattern used to target hosts in the ' +
                    'inventory. Leaving the field blank, all, and * will ' +
                    'all target all hosts in the inventory.  You can find ' +
                    'more information about Ansible\'s host patterns ' +
                    '<a id=\"adhoc_form_hostpatterns_doc_link\"' +
                    'href=\"http://docs.ansible.com/intro_patterns.html\" ' +
                    'target=\"_blank\">here</a>.</p>',
                dataTitle: i18n._('Limit'),
                dataPlacement: 'right',
                dataContainer: 'body'
            },
            credential: {
                label: i18n._('Machine Credential'),
                type: 'lookup',
                list: 'CredentialList',
                basePath: 'credentials',
                sourceModel: 'credential',
                sourceField: 'name',
                class: 'squeeze',
                ngClick: 'lookupCredential()',
                awPopOver: '<p>Select the credential you want to use when ' +
                    'accessing the remote hosts to run the command. ' +
                    'Choose the credential containing ' +
                    'the username and SSH key or password that Ansible ' +
                    'will need to log into the remote hosts.</p>',
                dataTitle: i18n._('Credential'),
                dataPlacement: 'right',
                dataContainer: 'body',
                awRequiredWhen: {
                    reqExpression: 'credRequired',
                    init: 'false'
                }
            },
            verbosity: {
                label: i18n._('Verbosity'),
                excludeModal: true,
                type: 'select',
                ngOptions: 'verbosity.label for verbosity in ' +
                    'adhoc_verbosity_options ' +
                    'track by verbosity.value',
                required: true,
                awPopOver:'<p>These are the verbosity levels for standard ' +
                    'out of the command run that are supported.',
                dataTitle: i18n._('Verbosity'),
                dataPlacement: 'right',
                dataContainer: 'body',
                "default": 1
            },
            forks: {
                label: i18n._('Forks'),
                id: 'forks-number',
                type: 'number',
                integer: true,
                min: 1,
                spinner: true,
                'class': "input-small",
                column: 1,
                awPopOver: '<p>' + i18n.sprintf(i18n._('The number of parallel or simultaneous processes to use while executing the playbook. Inputting no value will use ' +
                    'the default value from the %sansible configuration file%s.'), '' +
                    '<a id="ansible_forks_docs" href=\"http://docs.ansible.com/intro_configuration.html#the-ansible-configuration-file\" ' +
                    ' target=\"_blank\">', '</a>') +'</p>',
                placeholder: 'DEFAULT',
                dataTitle: i18n._('Forks'),
                dataPlacement: 'right',
                dataContainer: "body"
            },
            diff_mode: {
                label: i18n._('Show Changes'),
                type: 'toggleSwitch',
                toggleSource: 'diff_mode',
                dataTitle: i18n._('Show Changes'),
                dataPlacement: 'right',
                dataContainer: 'body',
                awPopOver: "<p>" + i18n._("If enabled, show the changes made by Ansible tasks, where supported. This is equivalent to Ansible&#x2019;s --diff mode.") + "</p>",
            },
            become_enabled: {
                label: i18n._('Enable Privilege Escalation'),
                type: 'checkbox',
                column: 2,
                awPopOver: "<p>If enabled,  run this playbook as an administrator. This is the equivalent of passing the<code> --become</code> option to the <code> ansible</code> command. </p>",
                dataPlacement: 'right',
                dataTitle: i18n._('Become Privilege Escalation'),
                dataContainer: "body"
            },
            extra_vars: {
                label: i18n._('Extra Variables'),
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                "default": "---",
                column: 2,
                awPopOver: "<p>" + i18n.sprintf(i18n._("Pass extra command line variables. This is the %s or %s command line parameter " +
                    "for %s. Provide key/value pairs using either YAML or JSON."), '<code>-e</code>', '<code>--extra-vars</code>', '<code>ansible</code>') + "</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n",
                dataTitle: i18n._('Extra Variables'),
                dataPlacement: 'right',
                dataContainer: "body"
            }
        },
        buttons: {
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true,
                label: i18n._('Reset'),
                'class': 'btn btn-sm Form-cancelButton'
            },
            launch: {
                label: i18n._('Save'),
                ngClick: 'launchJob()',
                ngDisabled: true,
                'class': 'btn btn-sm List-buttonSubmit launchButton'
            }
        },

        related: {}
    };
}];
