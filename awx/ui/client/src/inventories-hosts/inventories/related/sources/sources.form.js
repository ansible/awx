/*************************************************
 * Copyright (c) 2019 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['NotificationsList', 'i18n', function(NotificationsList, i18n){

    var notifications_object = {
        generateList: true,
        include: "NotificationsList",
        ngIf: "(sufficientRoleForNotif) && !(inventory_source_obj.source === undefined || inventory_source_obj.source === '')",
        ngClick: "$state.go('inventories.edit.inventory_sources.edit.notifications')"
    };
    let clone = _.clone(NotificationsList);
    notifications_object = angular.extend(clone, notifications_object);
    return {
        addTitle: i18n._('CREATE SOURCE'),
        editTitle: '{{ name }}',
        showTitle: true,
        name: 'inventory_source',
        basePath: 'inventory_sources',
        parent: 'inventories.edit.sources',
        // the parent node this generated state definition tree expects to attach to
        stateTree: 'inventories',
        tabs: true,
        // form generator inspects the current state name to determine whether or not to set an active (.is-selected) class on a form tab
        // this setting is optional on most forms, except where the form's edit state name is not parentStateName.edit
        activeEditState: 'inventories.edit.inventory_sources.edit',
        detailsClick: "$state.go('inventories.edit.inventory_sources.edit')",
        well: false,
        subFormTitles: {
            sourceSubForm: i18n._('Source Details'),
        },
        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                required: true,
                tab: 'properties'
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                tab: 'properties'
            },
            source: {
                label: i18n._('Source'),
                type: 'select',
                required: true,
                ngOptions: 'source.label for source in source_type_options track by source.value',
                ngChange: 'sourceChange(source)',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                ngModel: 'source',
                hasSubForm: true
            },
            custom_virtualenv: {
                label: i18n._('Ansible Environment'),
                type: 'select',
                defaultText: i18n._('Use Default Environment'),
                ngOptions: 'venv for venv in custom_virtualenvs_options track by venv',

                awPopOver: "<p>" + i18n._("Select the custom Python virtual environment for this inventory source sync to run on.") + "</p>",
                dataTitle: i18n._('Ansible Environment'),
                dataContainer: 'body',
                dataPlacement: 'right',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                ngShow: 'custom_virtualenvs_options.length > 1'
            },
            credential: {
                label: i18n._('Credential'),
                type: 'lookup',
                list: 'CredentialList',
                basePath: 'credentials',
                ngShow: "source && source.value !== ''",
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookupCredential()',
                awRequiredWhen: {
                    reqExpression: "cloudCredentialRequired",
                    init: "false"
                },
                subForm: 'sourceSubForm',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                watchBasePath: "credentialBasePath"
            },
            project: {
                // initializes a default value for this search param
                // search params with default values set will not generate user-interactable search tags
                label: i18n._('Project'),
                type: 'lookup',
                list: 'ProjectList',
                basePath: 'projects',
                ngShow: "source && source.value === 'scm'",
                sourceModel: 'project',
                sourceField: 'name',
                ngClick: 'lookupProject()',
                awRequiredWhen: {
                    reqExpression: "source && source.value === 'scm'",
                    init: "false"
                },
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                watchBasePath: "projectBasePath",
                subForm: 'sourceSubForm'
            },
            inventory_file: {
                label: i18n._('Inventory File'),
                type:'select',
                defaultText: i18n._('Choose an inventory file'),
                ngOptions: 'file for file in inventory_files track by file',
                ngShow: "source && source.value === 'scm'",
                ngDisabled: "!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd) || disableInventoryFileBecausePermissionDenied",
                id: 'inventory-file-select',
                awRequiredWhen: {
                    reqExpression: "source && source.value === 'scm'",
                    init: "true"
                },
                column: 1,
                awPopOver: "<p>" + i18n._("Select the inventory file to be synced by this source. " +
                            "You can select from the dropdown or enter a file within the input.") + "</p>",
                dataTitle: i18n._('Inventory File'),
                dataPlacement: 'right',
                dataContainer: "body",
                includeInventoryFileNotFoundError: true,
                subForm: 'sourceSubForm'
            },
            inventory_script: {
                label :  i18n._("Custom Inventory Script"),
                type: 'lookup',
                basePath: 'inventory_scripts',
                list: 'InventoryScriptsList',
                ngShow: "source && source.value === 'custom'",
                sourceModel: 'inventory_script',
                sourceField: 'name',
                awRequiredWhen: {
                    reqExpression: "source && source.value === 'custom'",
                    init: "false"
                },
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            custom_variables: {
                id: 'custom_variables',
                label: i18n._('Environment Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value=='custom' || source.value === 'scm'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Environment Variables"),
                dataPlacement: 'right',
                awPopOver:  "<p>" + i18n._("Provide environment variables to pass to the custom inventory script.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            ec2_variables: {
                id: 'ec2_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'ec2'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/amazon/aws/aws_ec2_inventory.html\" target=\"blank\">aws_ec2</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            vmware_variables: {
                id: 'vmware_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'vmware'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/community/vmware/vmware_vm_inventory_inventory.html\" target=\"blank\">vmware_vm_inventory</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            openstack_variables: {
                id: 'openstack_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'openstack'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/openstack/cloud/openstack_inventory.html\" target=\"blank\">openstack</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            cloudforms_variables: {
                id: 'cloudforms_variables',
                label: i18n._('Source Variables'),
                ngShow: "source && source.value == 'cloudforms'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: i18n._("Override variables found in cloudforms.ini and used by the inventory update script. For an example variable configuration") +
                    '<a href=\"https://github.com/ansible-collections/community.general/blob/main/scripts/inventory/cloudforms.ini\" target=\"_blank\">' +
                    i18n._("view cloudforms.ini in the Ansible Collections github repo.") + "</a>" + i18n._(" Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax."),
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            satellite6_variables: {
                id: 'satellite6_variables',
                label: i18n._('Source Variables'),
                ngShow: "source && source.value == 'satellite6'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/theforeman/foreman/foreman_inventory.html\" target=\"blank\">foreman</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            azure_rm_variables: {
                id: 'azure_rm_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'azure_rm'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/azure/azcollection/azure_rm_inventory.html\" target=\"blank\">azure_rm</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            gce_variables: {
                id: 'gce_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'gce'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/google/cloud/gcp_compute_inventory.html\" target=\"blank\">gcp_compute</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            tower_variables: {
                id: 'tower_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'tower'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/awx/awx/tower_inventory.html\" target=\"blank\">tower</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            rhv_variables: {
                id: 'rhv_variables',
                label: i18n._('Source Variables'), //"{{vars_label}}" ,
                ngShow: "source && source.value == 'rhv'",
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: i18n._("Source Variables"),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Enter variables to configure the inventory source. For a detailed description of how to configure this plugin, see ") +
                    "<a href=\"http://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html#inventory-plugins\" target=\"blank\">" +
                    i18n._("Inventory Plugins") + "</a> " + i18n._("in the documentation and the ") +
                    "<a href=\"https://docs.ansible.com/ansible/latest/collections/ovirt/ovirt/ovirt_inventory.html\" target=\"blank\">ovirt</a> " +
                    i18n._("plugin configuration guide.") + "</p>" +
                    "<p>" + i18n._("Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    i18n._("JSON:") + "<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    i18n._("YAML:") + "<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    "<p>" + i18n._("View JSON examples at ") + '<a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    "<p>" + i18n._("View YAML examples at ") + '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                subForm: 'sourceSubForm'
            },
            verbosity: {
                label: i18n._('Verbosity'),
                type: 'select',
                ngOptions: 'v.label for v in verbosity_options track by v.value',
                ngShow: "source && (source.value !== '' && source.value !== null)",
                disableChooseOption: true,
                column: 1,
                awPopOver: "<p>" + i18n._("Control the level of output ansible will produce for inventory source update jobs.") + "</p>",
                dataTitle: i18n._('Verbosity'),
                dataPlacement: 'right',
                dataContainer: "body",
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            host_filter: {
                label: i18n._("Host Filter"),
                type: 'text',
                dataTitle: i18n._('Host Filter'),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Regular expression where only matching host names will be imported. The filter is applied as a post-processing step after any inventory plugin filters are applied.") + "</p>",
                dataContainer: 'body',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            enabled_var: {
                label: i18n._("Enabled Variable"),
                type: 'text',
                dataTitle: i18n._('Enabled Variable'),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("Retrieve the enabled state from the given dict of host variables. The enabled variable may be specified using dot notation, e.g: 'foo.bar'") + "</p>",
                dataContainer: 'body',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            enabled_value: {
                label: i18n._("Enabled Value"),
                type: 'text',
                dataTitle: i18n._('Enabled Value'),
                dataPlacement: 'right',
                awPopOver: "<p>" + i18n._("This field is ignored unless an Enabled Variable is set. If the enabled variable matches this value, the host will be enabled on import.") + "</p>",
                dataContainer: 'body',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                subForm: 'sourceSubForm'
            },
            checkbox_group: {
                label: i18n._('Update Options'),
                type: 'checkbox_group',
                ngShow: "source && (source.value !== '' && source.value !== null)",
                subForm: 'sourceSubForm',
                fields: [{
                    name: 'overwrite',
                    label: i18n._('Overwrite'),
                    type: 'checkbox',
                    ngShow: "source.value !== '' && source.value !== null",
                    awPopOver: "<p>" + i18n._("If checked, any hosts and groups that were previously present on the external source but are now removed will be removed from the Tower inventory. Hosts and groups that were not managed by the inventory source will be promoted to the next manually created group or if there is no manually created group to promote them into, they will be left in the \"all\" default group for the inventory.") + '</p><p>' +
                                i18n._("When not checked, local child hosts and groups not found on the external source will remain untouched by the inventory update process.") + "</p>",
                    dataTitle: i18n._('Overwrite'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: "(!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd))"
                }, {
                    name: 'overwrite_vars',
                    label: i18n._('Overwrite Variables'),
                    type: 'checkbox',
                    ngShow: "source.value !== '' && source.value !== null",
                    awPopOver: "<p>" + i18n._("If checked, all variables for child groups and hosts will be removed and replaced by those found on the external source.") + '</p><p>' +
                                i18n._("When not checked, a merge will be performed, combining local variables with those found on the external source.") + "</p>",
                    dataTitle: i18n._('Overwrite Variables'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: "(!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd))"
                }, {
                    name: 'update_on_launch',
                    label: i18n._('Update on Launch'),
                    type: 'checkbox',
                    ngShow: "source.value !== '' && source.value !== null",
                    awPopOver: "<p>" + i18n._("Each time a job runs using this inventory, " +
                                "refresh the inventory from the selected source before executing job tasks.") + "</p>",
                    dataTitle: i18n._('Update on Launch'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)'
                }, {
                    name: 'update_on_project_update',
                    label: i18n._('Update on Project Update'),
                    type: 'checkbox',
                    ngShow: "source.value === 'scm'",
                    awPopOver: "<p>" + i18n._("After every project update where the SCM revision changes, " +
                                "refresh the inventory from the selected source before executing job tasks. " +
                                "This is intended for static content, like the Ansible inventory .ini file format.") + "</p>",
                    dataTitle: i18n._('Update on Project Update'),
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)'
                }]
            },
            update_cache_timeout: {
                label: i18n._("Cache Timeout") + " <span class=\"small-text\"> " + i18n._("(seconds)") + "</span>",
                id: 'source-cache-timeout',
                type: 'number',
                ngDisabled: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)',
                integer: true,
                min: 0,
                ngShow: "source && source.value !== '' && update_on_launch",
                spinner: true,
                "default": 0,
                awPopOver: "<p>" + i18n._("Time in seconds to consider an inventory sync to be current. " +
                        "During job runs and callbacks the task system will evaluate the timestamp of the latest sync. " +
                            "If it is older than Cache Timeout, it is not considered current, and a new inventory sync will be performed.") + "</p>",
                dataTitle: i18n._('Cache Timeout'),
                dataPlacement: 'right',
                dataContainer: "body",
                subForm: 'sourceSubForm'
            }
        },

        buttons: {
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()',
                ngDisabled: true,
                ngShow: '(inventory_source_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        },

        related: {
            notifications: notifications_object,
            schedules: {
                title: i18n._('Schedules'),
                skipGenerator: true,
                ngClick: "$state.go('inventories.edit.inventory_sources.edit.schedules')"
            }
        }

    };

}];
