/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Groups
 * @description This form is for adding/editing a Group on the inventory page
*/

export default ['i18n',
function(i18n){
    return {
        addTitle: i18n._('CREATE GROUP'),
        editTitle: '{{ name }}',
        showTitle: true,
        name: 'nested_group',
        iterator: "nested_group",
        basePath: 'groups',
        parent: 'inventories.edit.groups.edit.nested_groups',
        // the parent node this generated state definition tree expects to attach to
        stateTree: 'inventories',
        // form generator inspects the current state name to determine whether or not to set an active (.is-selected) class on a form tab
        // this setting is optional on most forms, except where the form's edit state name is not parentStateName.edit
        activeEditState: 'inventories.edit.groups.edit.nested_groups.edit',
        detailsClick: "$state.go('inventories.edit.groups.edit.nested_groups.edit')",
        well: false,
        tabs: true,
        fields: {
            name: {
                label: i18n._('Name'),
                type: 'text',
                ngDisabled: '!(group_obj.summary_fields.user_capabilities.edit || canAdd)',
                required: true,
                tab: 'properties'
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
                ngDisabled: '!(group_obj.summary_fields.user_capabilities.edit || canAdd)',
                tab: 'properties'
            },
            nested_group_variables: {
                realName: 'variables',
                label: i18n._('Variables'),
                type: 'textarea',
                class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                rows: 6,
                'default': '---',
                dataTitle: i18n._('Group Variables'),
                dataPlacement: 'right',
                parseTypeName: 'parseType',
                awPopOver: "<p>Variables defined here apply to all child groups and hosts.</p>" +
                    "<p>Enter variables using either JSON or YAML syntax. Use the " +
                    "radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />&emsp; \"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                tab: 'properties'
            }
        },

        buttons: {
            cancel: {
                ngClick: 'formCancel()',
                ngShow: '(group_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            close: {
                ngClick: 'formCancel()',
                ngShow: '!(group_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            save: {
                ngClick: 'formSave()',
                ngDisabled: true,
                ngShow: '(group_obj.summary_fields.user_capabilities.edit || canAdd)'
            }
        },
        related: {
            nested_groups: {
                name: 'related_groups',
                ngClick: "$state.go('inventories.edit.groups.edit.related_groups')",
                title: i18n._('Groups'),
                iterator: 'related_group'
            },

        }
    };
}];
