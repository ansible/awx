/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['i18n', function(i18n) {
        return {

        addTitle: i18n._('NEW SMART INVENTORY'),
        editTitle: '{{ inventory_name }}',
        name: 'smartinventory',
        basePath: 'inventory',
        breadcrumbName: 'SMART INVENTORY',
        stateTree: 'hosts',

        fields: {
            inventory_name: {
                realName: 'name',
                label: i18n._('Name'),
                type: 'text',
                required: true,
                capitalize: false,
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            inventory_description: {
                realName: 'description',
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            organization: {
                label: i18n._('Organization'),
                type: 'lookup',
                basePath: 'organizations',
                list: 'OrganizationList',
                sourceModel: 'organization',
                sourceField: 'name',
                awRequiredWhen: {
                    reqExpression: "organizationrequired",
                    init: "true"
                },
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd) || !canEditOrg',
                awLookupWhen: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd) && canEditOrg'
            },
            variables: {
                label: i18n._('Variables'),
                type: 'textarea',
                class: 'Form-formGroup--fullWidth',
                rows: 6,
                "default": "---",
                awPopOver: "<p>" + i18n._("Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>' + i18n.sprintf(i18n._('View JSON examples at %s'), '<a href="http://www.json.org" target="_blank">www.json.org</a>') + '</p>' +
                    '<p>' + i18n.sprintf(i18n._('View YAML examples at %s'), '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a>') + '</p>',
                dataTitle: i18n._('Inventory Variables'),
                dataPlacement: 'right',
                dataContainer: 'body',
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)' // TODO: get working
            }
        },

        buttons: {
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()',
                ngDisabled: true,
                ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        },
        related: {}

    };}];
