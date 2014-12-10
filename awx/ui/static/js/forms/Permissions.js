/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Permissions.js
 *
 *  Form definition for Projects model
 *
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:Permissions
 * @description This form is for adding/editing persmissions
*/
angular.module('PermissionFormDefinition', [])
    .value('PermissionsForm', {

        addTitle: 'Add Permission', //Title in add mode
        editTitle: '{{ name }}', //Title in edit mode
        name: 'permission', //entity or model name in singular form
        well: true, //Wrap the form with TB well
        forceListeners: true,

        stream: {
            'class': "btn-primary btn-xs activity-btn",
            ngClick: "showActivity()",
            awToolTip: "View Activity Stream",
            dataPlacement: "top",
            icon: "icon-comments-alt",
            mode: 'edit',
            iconSize: 'large'
        },

        fields: {
            category: {
                label: 'Permission Type',
                labelClass: 'prepend-asterisk',
                type: 'radio_group',
                options: [{
                    label: 'Inventory',
                    value: 'Inventory',
                    selected: true
                }, {
                    label: 'Job Template',
                    value: 'Deploy'
                }],
                ngChange: 'selectCategory()'
            },
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false
            },
            description: {
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
            },
            user: {
                label: 'User',
                type: 'hidden'
            },
            team: {
                label: 'Team',
                type: 'hidden'
            },
            project: {
                label: 'Project',
                type: 'lookup',
                sourceModel: 'project',
                sourceField: 'name',
                ngShow: "category == 'Deploy'",
                ngClick: 'lookUpProject()',
                awRequiredWhen: {
                    variable: "projectrequired",
                    init: "false"
                }
            },
            inventory: {
                label: 'Inventory',
                type: 'lookup',
                sourceModel: 'inventory',
                sourceField: 'name',
                ngClick: 'lookUpInventory()',
                awRequiredWhen: {
                    variable: "inventoryrequired",
                    init: "true"
                }
            },
            permission_type: {
                label: 'Permission',
                labelClass: 'prepend-asterisk',
                type: 'radio_group',
                options: [{
                    label: 'Read',
                    value: 'read',
                    ngShow: "category == 'Inventory'"
                }, {
                    label: 'Write',
                    value: 'write',
                    ngShow: "category == 'Inventory'"
                }, {
                    label: 'Admin',
                    value: 'admin',
                    ngShow: "category == 'Inventory'"
                }, {
                    label: 'Create',
                    value: 'create',
                    ngShow: "category == 'Deploy'"
                }, {
                    label: 'Run',
                    value: 'run',
                    ngShow: "category == 'Deploy'"
                }, {
                    label: 'Check',
                    value: 'check',
                    ngShow: "category == 'Deploy'"
                }],
                helpCollapse: [{
                    hdr: 'Permission',
                    ngBind: 'permissionTypeHelp'
                }]
            }
        },

        buttons: {
            save: {
                ngClick: 'formSave()',
                ngDisabled: true
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true
            }
        },

        related: { }

    }); // Form
