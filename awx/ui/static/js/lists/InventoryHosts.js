/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryHosts.js
 *
 *  Right side of /inventories/N page, showing hosts in the selected group.
 *
 */



export default
    angular.module('InventoryHostsDefinition', [])
    .value('InventoryHosts', {

        name: 'hosts',
        iterator: 'host',
        editTitle: '{{ selected_group }}',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        hasChildren: true,
        'class': 'table-no-border',
        multiSelect: true,

        fields: {
            name: {
                key: true,
                label: 'Hosts',
                ngClick: "editHost(host.id)",
                ngClass: "{ 'host-disabled-label': !host.enabled }",
                columnClass: 'col-lg-6 col-md-8 col-sm-8 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host"
            },
            enabled: {
                label: 'Disabled?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'false',
                searchOnly: true
            },
            has_active_failures: {
                label: 'Failed jobs?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
            }
        },

        fieldActions: {

            columnClass: 'col-lg-6 col-md-4 col-sm-4 col-xs-5 text-right',
            label: false,

            active_failures: {
                awPopOver: "{{ host.job_status_html }}",
                dataTitle: "{{ host.job_status_title }}",
                awToolTip: "{{ host.badgeToolTip }}",
                awTipPlacement: 'top',
                dataPlacement: 'left',
                iconClass: "{{ 'fa icon-job-' + host.active_failures }}",
                id: 'active-failutes-action'
            },
            edit: {
                //label: 'Edit',
                ngClick: "editHost(host.id)",
                icon: 'icon-edit',
                awToolTip: 'Edit host',
                dataPlacement: 'top'
            },
            copy: {
                mode: 'all',
                ngClick: "copyHost(host.id)",
                awToolTip: 'Copy or move host to another group',
                dataPlacement: "top"
            },
            "delete": {
                //label: 'Delete',
                ngClick: "deleteHost(host.id, host.name)",
                icon: 'icon-trash',
                awToolTip: 'Delete host',
                dataPlacement: 'top'
            }
        },

        actions: {
            system_tracking: {
                label: 'System Tracking',
                ngClick: 'systemTracking()', //'editInventoryProperties(inventory.id)',
                awToolTip: "{{ systemTrackingTooltip }}",
                dataTipWatch: "systemTrackingTooltip",
                dataPlacement: 'top',
                awFeature: 'system_tracking',
                ngDisabled: 'systemTrackingDisabled',
                ngShow: 'hostsSelected'
            },
            create: {
                mode: 'all',
                ngClick: "createHost()",
                awToolTip: "Create a new host"
            },
            refresh: {
                mode: 'all',
                awToolTip: "Refresh the page",
                ngClick: "refreshGroups()",
                ngShow: "socketStatus == 'error'"
            },
            stream: {
                ngClick: "showHostActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all',
                awFeature: 'activity_streams'
            },
        }

    });
