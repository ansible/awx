/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobHosts.js 
 *  List view object for Job Host Summary data model.
 *
 * 
 */
angular.module('JobHostDefinition', [])
    .value(
    'JobHostList', {
        
        name: 'jobhosts',
        iterator: 'jobhost',
        editTitle: 'Job Host Summary',
        index: true,
        hover: true,
        
        fields: {
            host: {
                label: 'Host',
                key: true,
                sourceModel: 'host',
                sourceField: 'name',
                ngBind: 'jobhost.host_name',
                ngClick:"showEvents('\{\{ jobhost.summary_fields.host.name \}\}','\{\{ jobhost.related.job \}\}')"
                },
             ok: {
                label: 'Success',
                searchable: false
                },
            changed: {
                label: 'Changed',
                searchable: false
                },
            failures: {
                label: 'Failure',
                searchType: 'gtzero'
                },
            dark: {
                label: 'Unreachable',
                searchable: false
                },
            skipped: {
                label: 'Skipped',
                searchable: false
                }
            },
        
        actions: {
            refresh: {
                label: 'Refresh',
                icon: 'icon-refresh',
                ngClick: "refresh()",
                "class": 'btn-success btn-small',
                awToolTip: 'Refresh the page',
                mode: 'all'
                },
            edit: {
                label: 'Details',
                icon: 'icon-edit',
                ngClick: "jobDetails()",
                "class": 'btn btn-small',
                awToolTip: 'Edit job details',
                mode: 'all'
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                ngClick: "jobEvents()",
                "class": 'btn btn-small',
                awToolTip: 'View job events',
                mode: 'all'            
                }
            },

        fieldActions: {
            }

        });
