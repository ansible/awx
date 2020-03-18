/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name forms.function:Inventories
 * @description This form is for adding/editing an inventory
 */

export default ['i18n',
function(i18n) {
    return {

        addTitle: i18n._('NEW INVENTORY'),
        editTitle: '{{ inventory_name }}',
        name: 'inventory',
        basePath: 'inventory',
        // the top-most node of this generated state tree
        stateTree: 'inventories',
        tabs: true,

        fields: {
            name: {
                realName: 'name',
                label: i18n._('Name'),
                type: 'text',
                required: true,
                capitalize: false,
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'
            },
            description: {
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
                required: true,
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd) || !canEditOrg',
                awLookupWhen: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd) && canEditOrg'
            },
            insights_credential: {
                label: i18n._('Insights Credential'),
                type: 'lookup',
                list: 'CredentialList',
                basePath: 'credentials',
                sourceModel: 'insights_credential',
                sourceField: 'name',
                ngDisabled: '!(inventory_obj.summary_fields.user_capabilities.edit || canAdd) || !canEditOrg',
            },
            instance_groups: {
                label: i18n._('Instance Groups'),
                type: 'custom',
                awPopOver: i18n._('Select the Instance Groups for this Inventory to run on. Refer to the Ansible Tower documentation for more detail.'),
                dataTitle: i18n._('Instance Groups'),
                dataPlacement: 'right',
                dataContainer: 'body',
                control: '<instance-groups-multiselect instance-groups="instance_groups" field-is-disabled="!(inventory_obj.summary_fields.user_capabilities.edit || canAdd)"></instance-groups-multiselect>',
            },
            variables: {
                label: i18n._('Variables'),
                type: 'code_mirror',
                class: 'Form-formGroup--fullWidth',
                variables: 'variables',
                awPopOver: i18n._('Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax.'),
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
        related: {
            permissions: {
                name: 'permissions',
                awToolTip: i18n._('Please save before assigning permissions.'),
                dataPlacement: 'top',
                basePath: 'api/v2/inventories/{{$stateParams.inventory_id}}/access_list/',
                type: 'collection',
                title: i18n._('Permissions'),
                iterator: 'permission',
                index: false,
                open: false,
                search: {
                    order_by: 'username'
                },
                actions: {
                    add: {
                        label: i18n._('Add'),
                        ngClick: "$state.go('.add')",
                        awToolTip: i18n._('Add a permission'),
                        actionClass: 'at-Button--add',
                        actionId: 'button-add--permission',
                        ngShow: '(inventory_obj.summary_fields.user_capabilities.edit || canAdd)'

                    }
                },
                fields: {
                    username: {
                        key: true,
                        label: i18n._('User'),
                        linkBase: 'users',
                        columnClass: 'col-sm-3 col-xs-4'
                    },
                    role: {
                        label: i18n._('Role'),
                        type: 'role',
                        nosort: true,
                        columnClass: 'col-sm-4 col-xs-4'
                    },
                    team_roles: {
                        label: i18n._('Team Roles'),
                        type: 'team_roles',
                        nosort: true,
                        columnClass: 'col-sm-5 col-xs-4'
                    }
                }
            },
            groups: {
                name: 'groups',
                awToolTip: i18n._('Please save before creating groups.'),
                dataPlacement: 'top',
                include: "GroupList",
                title: i18n._('Groups'),
                iterator: 'group',
                tabSelected: `$state.includes('inventories.edit.groups') || $state.includes('inventories.edit.rootGroups')`,
                skipGenerator: true
            },
            hosts: {
                name: 'hosts',
                awToolTip: i18n._('Please save before creating hosts.'),
                dataPlacement: 'top',
                include: "RelatedHostsListDefinition",
                title: i18n._('Hosts'),
                iterator: 'host',
                skipGenerator: true
            },
            inventory_sources: {
                name: 'inventory_sources',
                awToolTip: i18n._('Please save before defining inventory sources.'),
                dataPlacement: 'top',
                title: i18n._('Sources'),
                iterator: 'inventory_source',
                skipGenerator: true
            },
            completed_jobs: {
                title: i18n._('Completed Jobs'),
                skipGenerator: true
            }
        },
        relatedButtons: {
            remediate_inventory: {
                ngClick: 'remediateInventory(id, insights_credential)',
                ngShow: "is_insights && mode !== 'add' && canRemediate && ($state.is('inventories.edit') || $state.is('inventories.edit.hosts'))",
                label: i18n._('Remediate Inventory'),
                class: 'Form-primaryButton'
            }
        }

    };}];
