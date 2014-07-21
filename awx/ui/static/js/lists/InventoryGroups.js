/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryGroups.js
 *
 */
angular.module('InventoryGroupsDefinition', [])
    .value('InventoryGroups', {

        name: 'groups',
        iterator: 'group',
        editTitle: '{{ inventory.name }}',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        'class': 'table-no-border',

        fields: {
            name: {
                label: 'Groups',
                key: true,
                ngClick: "groupSelect(group.id)",
                columnClick: "groupSelect(group.id)",
                columnClass: 'col-lg-8 col-md-8 col-sm-8 col-xs-6'
            },
            source: {
                label: 'Source',
                searchType: 'select',
                searchOptions: [{
                    name: "ec2",
                    value: "ec2"
                }, {
                    name: "none",
                    value: ""
                }, {
                    name: "rax",
                    value: "rax"
                }],
                sourceModel: 'inventory_source',
                sourceField: 'source',
                searchOnly: true
            },
            has_external_source: {
                label: 'Has external source?',
                searchType: 'in',
                searchValue: 'ec2,rax',
                searchOnly: true,
                sourceModel: 'inventory_source',
                sourceField: 'source'
            },
            has_active_failures: {
                label: 'Has failed hosts?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            },
            last_update_failed: {
                label: 'Update failed?',
                searchType: 'select',
                searchSingleValue: true,
                searchValue: 'failed',
                searchOnly: true,
                sourceModel: 'inventory_source',
                sourceField: 'status'
            }
        },

        actions: {
            create: {
                mode: 'all',
                ngClick: "createGroup()",
                awToolTip: "Create a new group"
            },
            properties: {
                mode: 'all',
                awToolTip: "Edit inventory properties",
                ngClick: 'editInventoryProperties()'
            },
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'"
            },
            stream: {
                ngClick: "showGroupActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all'
            },
            help: {
                mode: 'all',
                awToolTip: "Get help building your inventory",
                ngClick: "showGroupHelp()",
                id: "inventory-summary-help"
            }
        },

        fieldActions: {

            columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6 text-right',
            label: false,

            sync_status: {
                mode: 'all',
                ngClick: "viewUpdateStatus(group.id)",
                awToolTip: "{{ group.status_tooltip }}",
                dataTipWatch: "group.status_tooltip",
                iconClass: "{{ 'fa icon-cloud-' + group.status_class }}",
                ngClass: "group.status_class",
                dataPlacement: "top"
            },
            failed_hosts: {
                mode: 'all',
                awToolTip: "{{ group.hosts_status_tip }}",
                dataPlacement: "top",
                ngClick: "showHosts(group.id, group.group_id, group.show_failures)",
                iconClass: "{{ 'fa icon-job-' + group.hosts_status_class }}"
            },
            group_update: {
                //label: 'Sync',
                mode: 'all',
                ngClick: 'updateGroup(group.id)',
                awToolTip: "{{ group.launch_tooltip }}",
                dataTipWatch: "group.launch_tooltip",
                ngShow: "group.status !== 'running' && group.status !== 'pending' && group.status !== 'updating'",
                ngClass: "group.launch_class",
                dataPlacement: "top"
            },
            cancel: {
                //label: 'Cancel',
                mode: 'all',
                ngClick: "cancelUpdate(group.id)",
                awToolTip: "Cancel sync process",
                'class': 'red-txt',
                ngShow: "group.status == 'running' || group.status == 'pending' || group.status == 'updating'",
                dataPlacement: "top"
            },
            edit: {
                //label: 'Edit',
                mode: 'all',
                ngClick: "editGroup(group.id)",
                awToolTip: 'Edit group',
                dataPlacement: "top"
            },
            copy: {
                mode: 'all',
                ngClick: "copyGroup(group.id)",
                awToolTip: 'Copy or move group',
                ngShow: "group.id > 0",
                dataPlacement: "top"
            },
            "delete": {
                //label: 'Delete',
                mode: 'all',
                ngClick: "deleteGroup(group.id)",
                awToolTip: 'Delete group',
                dataPlacement: "top"
            }
        }
    });