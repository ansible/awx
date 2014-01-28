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
                columnClass: 'col-lg-9 ellipsis',
                dataHostId: "\{\{ host.id \}\}",
                dataType: "host",
                awDraggable: "true"
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
                label: 'Failed jobs?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true
                }
            },
        
        fieldActions: {
            enabled_flag: {
                //label: 'Enabled',
                iconClass: "{{ 'fa icon-enabled-' + host.enabled }}",
                dataPlacement: 'top',
                awToolTip: "{{ host.enabledToolTip }}",
                dataTipWatch: "host.enabledToolTip",
                ngClick: "toggleHostEnabled(host.id, host.has_inventory_sources)"
                },
            active_failures: {
                //label: 'Job Status',
                //ngHref: "\{\{'/#/hosts/' + host.id + '/job_host_summaries/?inventory=' + inventory_id \}\}",
                awPopOver: "{{ host.job_status_html }}",
                dataTitle: "{{ host.job_status_title }}",
                awToolTip: "{{ host.badgeToolTip }}",
                awTipPlacement: 'top',
                dataPlacement: 'left',
                iconClass: "{{ 'fa icon-failures-' + host.has_active_failures }}"
                },
            edit: {
                //label: 'Edit',
                ngClick: "editHost(\{\{ host.id \}\})",
                icon: 'icon-edit',
                awToolTip: 'Edit host',
                dataPlacement: 'top'
                },
            "delete": {
                //label: 'Delete',
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-trash',
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
            