/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  HomeHosts.js 
 *
 *  List view object for Hosts data model. Used
 *  on the home tab.
 *  
 */
angular.module('HomeHostListDefinition', [])
    .value(
    'HomeHostList', {
        
        name: 'hosts',
        iterator: 'host',
        selectTitle: 'Add Existing Hosts',
        editTitle: 'Hosts',
        index: true,
        well: true,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-3 col-md3 col-sm-2',
                ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')"
                },
            inventory_name: {
                label: 'Inventory', 
                sourceModel: 'inventory',
                sourceField: 'name',
                columnClass: 'col-lg-3 col-md3 col-sm-2',
                linkTo: "\{\{ '/#/inventories/' + group.inventory \}\}"
                },
            active_failures: {
                label: 'Job Status',
                ngHref: "\{\{ host.activeFailuresLink \}\}", 
                awToolTip: "\{\{ host.badgeToolTip \}\}",
                dataPlacement: 'top',
                badgeNgHref: '\{\{ host.activeFailuresLink \}\}', 
                badgeIcon: "\{\{ 'icon-failures-' + host.has_active_failures \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ host.badgeToolTip \}\}",
                badgeTipPlacement: 'top',
                searchable: false,
                nosort: true
                },
            enabled_flag: {
                label: 'Enabled',
                badgeIcon: "\{\{ 'icon-enabled-' + host.enabled \}\}", 
                badgePlacement: 'left',
                badgeToolTip: "\{\{ host.enabledToolTip \}\}",
                badgeTipPlacement: "top",
                ngClick: "toggle_host_enabled(\{\{ host.id \}\}, \{\{ host.has_inventory_sources \}\})",
                searchable: false,
                showValue: false
                },
            groups: {
                label: 'Groups',
                searchable: true,
                sourceModel: 'groups',
                sourceField: 'name',
                nosort: true
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
        
        actions: {
            },

        fieldActions: {
            }
        });
