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
                label: 'Host Name',
                ngClick: "editHost(\{\{ host.id \}\}, '\{\{ host.name \}\}')",
                badgeIcon: "\{\{ 'icon-failures-' + host.has_active_failures \}\}",
                badgeToolTip: 'Indicates if host has active failures',
                badgePlacement: 'left',
                badgeTipPlacement: 'bottom',
                columnClass: 'col-lg-3'
                },
            groups: {
                label: 'Groups',
                searchable: false,
                sourceModel: 'groups',
                sourceField: 'name',
                nosort: true
                },
            dropdown: {
                type: 'DropDown',
                searchable: false,
                nosort: true,
                label: 'Jobs',
                "class": "btn-sm",
                //ngDisabled: 'host.last_job == null',
                options: [
                    { ngClick: "allJobs(\{\{ host.id \}\})", label: 'All jobs', ngShow: 'host.last_job' },
                    { ngClick: "allHostSummaries(\{\{ host.id \}\},'\{\{ host.name \}\}', \{\{ inventory_id \}\})", label: 'All host summaries', 
                        ngShow: 'host.last_job' },
                    { ngClick: 'viewJobs(\{\{ host.last_job \}\})', label: 'Latest job', ngShow: 'host.last_job' },
                    { ngClick: "viewLastEvents(\{\{ host.id \}\}, '\{\{ host.last_job \}\}', '\{\{ host.name \}\}', " +
                        "'\{\{ host.summary_fields.last_job.name \}\}')", label: 'Latest job events', ngShow: 'host.last_job' },
                    { ngClick: "viewLastSummary(\{\{ host.id \}\}, '\{\{ host.last_job \}\}', '\{\{ host.name \}\}', " +
                        "'\{\{ host.summary_fields.last_job.name \}\}')", label: 'Latest host summary', ngShow: 'host.last_job' },
                    { ngClick: "", label: 'No job data available', ngShow: 'host.last_job == null' }
                    ]
                }
            },

        actions: {
            add: {
                label: 'Copy',
                ngClick: "addHost()",
                ngHide: "hostAddHide",
                awToolTip: "Copy an existing host to the selected group",
                dataPlacement: 'bottom',
                'class': 'btn-sm btn-success',
                icon: 'icon-check'
                },
            create: {
                label: 'Create New',
                ngClick: 'createHost()',
                ngHide: 'hostCreateHide',
                awToolTip: 'Create a new host and add it to the selected group',
                dataPlacement: 'bottom',
                'class': 'btn-sm btn-success',
                icon: 'icon-plus'
                }
            },
        
        fieldActions: {
            "delete": {
                ngClick: "deleteHost(\{\{ host.id \}\},'\{\{ host.name \}\}')",
                icon: 'icon-trash',
                "class": 'btn-sm btn-danger',
                awToolTip: 'Delete host'
                }
            }
     
    }); //InventoryHostsForm