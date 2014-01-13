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
        hover: false,
        hasChildren: true,
        'class': 'table-condensed table-no-border',
        
        fields: {
            name: {
                key: true,
                label: 'Hosts',
                ngClick: "editHost(\{\{ host.id \}\})",
                searchPlaceholder: "search_place_holder",
                columnClass: 'col-lg-9'
                },
            /*groups: {
                label: 'Groups',
                searchable: true,
                sourceModel: 'groups',
                sourceField: 'name',
                nosort: true,
                searchPlaceholder: "search_place_holder"
                },*/
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
                }
            /*    ,
            has_inventory_sources: {
                label: 'Has external source?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                }*/
            },
        
        fieldActions: {
            enabled_flag: {
                //label: 'Enabled',
                iconClass: "\{\{ 'fa icon-enabled-' + host.enabled \}\}", 
                dataPlacement: 'top',
                awToolTip: "\{\{ host.enabledToolTip \}\}",
                dataTipWatch: "host.enabledToolTip",
                ngClick: "toggleHostEnabled(\{\{ host.id \}\}, \{\{ host.has_inventory_sources \}\})"
                },
            active_failures: {
                //label: 'Job Status',
                awToolTip: "\{\{ host.badgeToolTip \}\}",
                dataPlacement: 'top',
                iconClass: "\{\{ 'fa icon-failures-' + host.has_active_failures \}\}"
                },
            edit: {
                //label: 'Edit',
                ngClick: "editHost(\{\{ host.id \}\})",
                icon: 'icon-edit',
                "class": 'btn-xs btn-primary',
                awToolTip: 'Edit host',
                dataPlacement: 'top'
                },
            "delete": {
                //label: 'Delete',
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-xs btn-primary',
                awToolTip: 'Delete host',
                dataPlacement: 'top'
                }
            },

        actions: {
            create: {
                mode: 'all',
                ngClick: "createHost()",
                ngHide: 'selected_tree_id == 1',   //disable when 'All Hosts' selected
                awToolTip: "Create a new host"
                },
            stream: {
                mode: 'all',
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                ngShow: "user_is_superuser"
                },
             help: {
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
            