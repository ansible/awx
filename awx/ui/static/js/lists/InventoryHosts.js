/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryHosts.js
 *
 *  Right side of /inventories/N page, showing hosts in the selected group.
 *
 */

'use strict';

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

        fields: {
            name: {
                key: true,
                label: 'Hosts',
                ngClick: "editHost(host.id)",
                searchPlaceholder: "search_place_holder",
                columnClass: 'col-lg-10 col-md-10 col-sm-10 col-xs-7',
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

            columnClass: 'col-lg-2 col-md-2 col-sm-2 col-xs-5',
            label: false,

            enabled_flag: {
                iconClass: "{{ 'fa icon-enabled-' + host.enabled }}",
                dataPlacement: 'top',
                awToolTip: "{{ host.enabledToolTip }}",
                dataTipWatch: "host.enabledToolTip",
                ngClick: "toggleHostEnabled(host.id, host.has_inventory_sources)"
            },
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
            create: {
                mode: 'all',
                ngClick: "createHost()",
                ngHide: '!selected_group_id', //disable when 'All Hosts' selected
                awToolTip: "Create a new host"
            },
            stream: {
                ngClick: "showHostActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all'
            }
        }

    });