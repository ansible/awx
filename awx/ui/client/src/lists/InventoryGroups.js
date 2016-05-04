/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    angular.module('InventoryGroupsDefinition', [])
    .value('InventoryGroups', {

        name: 'groups',
        iterator: 'group',
        editTitle: '{{ inventory.name }}',
        listTitle: 'Groups',
        searchSize: 'col-lg-12 col-md-12 col-sm-12 col-xs-12',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        'class': 'table-no-border',
        multiSelect: true,

        fields: {
            name: {
                label: 'Groups',
                key: true,
                ngClick: "groupSelect(group.id)",
                columnClick: "groupSelect(group.id)",
                columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-3'
            },
            total_groups: {
                nosort: true,
                label: '',
                type: 'badgeCount',
                ngHide: 'group.total_groups == 0',
            },
            source: {
                label: 'Source',
                searchType: 'select',
                searchOptions: [{
                    name: "Amazon Web Services",
                    value: "ec2"
                }, {
                    name: "none",
                    value: ""
                }, {
                    name: "Rackspace",
                    value: "rax"
                },{
                    name: "VMware",
                    value: "vmware"
                },{
                    name: "Google Compute Engine",
                    value: "gce"
                },{
                    name: "Microsoft Azure",
                    value: "azure"
                },{
                    name: "OpenStack",
                    value: "openstack"
                }],
                sourceModel: 'inventory_source',
                sourceField: 'source',
                searchOnly: true
            },
            has_external_source: {
                label: 'Has external source?',
                searchType: 'in',
                searchValue: 'ec2,rax,vmware,azure,gce,openstack',
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
                searchType: 'boolean',
                searchSingleValue: true,
                searchValue: 'failed',
                searchOnly: true,
                sourceModel: 'inventory_source',
                sourceField: 'status'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'REFRESH'
            },
            launch: {
                mode: 'all',
                ngShow: 'inventory.can_run_ad_hoc_commands',
                ngClick: 'populateAdhocForm()',
                awToolTip: "Run a command on the selected inventory",
                actionClass: 'btn List-buttonDefault',
                buttonContent: 'RUN COMMANDS'
                // TODO: set up a tip watcher and change text based on when
                // things are selected/not selected.  This is started and
                // commented out in the inventory controller within the watchers.
                // awToolTip: "{{ adhocButtonTipContents }}",
                // dataTipWatch: "adhocButtonTipContents"
            },
            create: {
                mode: 'all',
                ngClick: "createGroup()",
                awToolTip: "Create a new group",
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-6 col-sm-6 col-xs-6 text-right',

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
                ngShow: "group.status !== 'running' && group.status " +
                    "!== 'pending' && group.status !== 'updating'",
                ngClass: "group.launch_class",
                dataPlacement: "top"
            },
            cancel: {
                //label: 'Cancel',
                mode: 'all',
                ngClick: "cancelUpdate(group.id)",
                awToolTip: "Cancel sync process",
                'class': 'red-txt',
                ngShow: "group.status == 'running' || group.status == 'pending' " +
                    "|| group.status == 'updating'",
                dataPlacement: "top"
            },
            copy: {
                mode: 'all',
                ngClick: "copyGroup(group.id)",
                awToolTip: 'Copy or move group',
                ngShow: "group.id > 0",
                dataPlacement: "top"
            },
            schedule: {
                mode: 'all',
                ngClick: "scheduleGroup(group.id)",
                awToolTip: "{{ group.group_schedule_tooltip }}",
                ngClass: "group.scm_type_class",
                dataPlacement: 'top',
                ngHide: "group.summary_fields.inventory_source.source === ''"
            },
            edit: {
                //label: 'Edit',
                mode: 'all',
                ngClick: "editGroup(group.id)",
                awToolTip: 'Edit group',
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
