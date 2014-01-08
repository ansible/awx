/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryHosts.js 
 *
 *  Right side of /inventories/N page, showing hosts in the selected group.
 * 
 */
angular.module('InventoryHostsDefinition', [])
    .value(
    'InventoryHosts', {

        name: 'hosts',
        iterator: 'host',
        editTitle: '{{ selected_group }}',
        showTitle: false,
        well: true,
        index: false,
        hover: true,
        hasChildren: true,
        'class': 'table-condensed',
        
        fields: {
            name: {
                key: true,
                label: 'Name',
                ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')",
                searchPlaceholder: "search_place_holder"
                },
            active_failures: {
                label: 'Job Status',
                ngHref: "\{\{ host.activeFailuresLink \}\}", 
                awToolTip: "\{\{ host.badgeToolTip \}\}",
                dataPlacement: 'top',
                badgeNgHref: '\{\{ host.activeFailuresLink \}\}', 
                badgeIcon: "\{\{ 'fa icon-failures-' + host.has_active_failures \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ host.badgeToolTip \}\}",
                badgeTipPlacement: 'top',
                searchable: false,
                nosort: true
                },
            enabled_flag: {
                label: 'Enabled',
                badgeIcon: "\{\{ 'fa icon-enabled-' + host.enabled \}\}", 
                badgePlacement: 'left',
                badgeToolTip: "\{\{ host.enabledToolTip \}\}",
                badgeTipPlacement: "top",
                badgeTipWatch: "host.enabledToolTip",
                ngClick: "toggle_host_enabled(\{\{ host.id \}\}, \{\{ host.has_inventory_sources \}\})",
                searchable: false,
                showValue: false
                },
            groups: {
                label: 'Groups',
                searchable: true,
                sourceModel: 'groups',
                sourceField: 'name',
                nosort: true,
                searchPlaceholder: "search_place_holder"
                },
            enabled: {
                label: 'Disabled?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'false',
                searchOnly: true
                },
            has_active_failures: {
                label: 'Has failed jobs?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                },
            has_inventory_sources: {
                label: 'Has external source?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                }
            },
        
        fieldActions: {
             edit: {
                label: 'Edit',
                ngClick: "editGroup(\{\{ group.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-primary',
                awToolTip: 'Edit host'
                },
            "delete": {
                label: 'Delete',
                ngClick: "deleteGroup(\{\{ group.id \}\},'\{\{ group.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-primary',
                awToolTip: 'Delete host'
                }
            },

        actions: {
            create: {
                mode: 'all',
                ngClick: "createHost()",
                ngHide: "hostCreateHide", 
                ngDisabled: 'BtnDisabled',
                awToolTip: "Create a new host"
                },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                mode: 'all',
                ngShow: "user_is_superuser"
                },
             help: {
                dataPlacement: 'top',
                mode: 'all',
                awToolTip:
                    //"<div style=\"text-align:left;\"><img src=\"/static/img/cow.png\" style=\"width:50px; height:56px; float:left; padding-right:5px;\">" +
                    //"<p>Need help getting started creating your inventory?</p><p>Click here for help.</p></div>",
                    "<div style=\"text-align:left;\"><p>Need help getting started creating your inventory?</p><p>Click here for help.</p></div>",
                ngClick: "showHelp()",
                id: "inventory-summary-help"
                }
            }

    });
            