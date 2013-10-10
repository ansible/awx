/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventoryHosts.js
 *  Form definition for Hosts model
 *
 * 
 */
angular.module('InventoryHostsFormDefinition', [])
    .value(
    'InventoryHostsForm', {
        
        type: 'hostsview',
        title: "groupTitle",
        editTitle: 'Hosts',
        iterator: 'host',
        
        fields: {
            name: {
                key: true,
                label: 'Name',
                ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')"
                },
            active_failures: {
                label: 'Current<br>Job Status?',
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
            inventory_sources: {
                label: 'External<br>Source?',
                ngHref: "\{\{ host.has_inv_source_link \}\}",
                badgeNgHref: "\{\{ host.has_inv_source_link \}\}",
                badgeIcon: "\{\{ 'icon-cloud-' + host.has_inventory_sources \}\}",
                badgePlacement: 'left',
                badgeToolTip: "\{\{ host.has_inv_source_tip \}\}",
                awToolTip: "\{\{ host.has_inv_source_tip \}\}",
                dataPlacement: 'top',
                badgeTipPlacement: 'top',
                searchable: false,
                nosort: true
                },
            groups: {
                label: 'Groups',
                searchable: true,
                sourceModel: 'groups',
                sourceField: 'name',
                nosort: true
                },
            has_active_failures: {
                label: 'Current job failed?',
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
            add: {
                label: 'Copy',
                ngClick: "addHost()",
                ngHide: "hostAddHide",
                awToolTip: "Copy an existing host to the selected group",
                dataPlacement: 'bottom',
                'class': 'btn-xs btn-success',
                icon: 'icon-check'
                },
            create: {
                label: 'Create New',
                ngClick: 'createHost()',
                ngHide: 'hostCreateHide',
                awToolTip: 'Create a new host and add it to the selected group',
                dataPlacement: 'bottom',
                'class': 'btn-xs btn-success',
                icon: 'icon-plus'
                }
            },
        
        fieldActions: {
            
            ViewJobs: {
                type: 'DropDown',
                label: 'Jobs',
                icon: 'icon-zoom-in',
                "class": "btn-default btn-sm",
                options: [
                    { ngClick: "allJobs(\{\{ host.id \}\})", label: 'All', ngShow: 'host.last_job' },
                    { ngClick: "allHostSummaries(\{\{ host.id \}\},'\{\{ host.name \}\}', \{\{ inventory_id \}\})", label: 'All summaries', 
                        ngShow: 'host.last_job' },
                    { ngClick: 'viewJobs(\{\{ host.last_job \}\})', label: 'Latest', ngShow: 'host.last_job' },
                    { ngClick: "viewLastEvents(\{\{ host.id \}\}, '\{\{ host.last_job \}\}', '\{\{ host.name \}\}', " +
                        "'\{\{ host.summary_fields.last_job.name \}\}')", label: 'Latest events', ngShow: 'host.last_job' },
                    { ngClick: "viewLastSummary(\{\{ host.id \}\}, '\{\{ host.last_job \}\}', '\{\{ host.name \}\}', " +
                        "'\{\{ host.summary_fields.last_job.name \}\}')", label: 'Latest summary', ngShow: 'host.last_job' },
                    { ngClick: "", label: 'No job data available', ngShow: 'host.last_job == null' }
                    ]
                },

            "delete": {
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-sm btn-danger',
                awToolTip: 'Delete host'
                }
            }
     
    }); //InventoryHostsForm
