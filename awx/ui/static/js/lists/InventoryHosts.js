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
        hover: false,
        hasChildren: true,
        'class': 'table-condensed table-no-border',

        fields: {
            name: {
                key: true,
                label: 'Hosts',
                ngClick: "editHost(host.id)",
                searchPlaceholder: "search_place_holder",
                columnClass: 'col-lg-9 col-md-9 col-sm-7 col-xs-7',
                dataHostId: "{{ host.id }}",
                dataType: "host",
                awDraggable: "true"
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
                iconClass: "{{ 'fa icon-failures-' + host.has_active_failures }}",
                id: 'active-failutes-action'
            },
            edit: {
                //label: 'Edit',
                ngClick: "editHost(host.id)",
                icon: 'icon-edit',
                awToolTip: 'Edit host',
                dataPlacement: 'top'
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

            columnClass: 'col-lg-3 col-md-3 col-sm-5 col-xs-5',

            create: {
                mode: 'all',
                ngClick: "createHost()",
                ngHide: 'selected_tree_id == 1', //disable when 'All Hosts' selected
                awToolTip: "Create a new host"
            },
            stream: {
                ngClick: "showHostActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all'
            }
        }

    });