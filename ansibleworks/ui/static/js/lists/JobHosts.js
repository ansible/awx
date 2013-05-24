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
                //linkTo: '/hosts/\{\{ jobhost.host \}\}'
                ngClick:"viewHost(\{\{ jobhost.host \}\})"
                },
            changed: {
                label: 'Changed',
                searchType: 'math'
                },
            dark: {
                label: 'Dark',
                searchType: 'math'
                },
            failures: {
                label: 'Failures',
                searchType: 'math'
                },
            ok: {
                label: 'OK',
                searchType: 'math'
                },
            processed: {
                label: 'Processed',
                searchType: 'math'
                },
            skipped: {
                label: 'Skipped',
                searchType: 'math'
                }
            },
        
        actions: {
            refresh: {
                label: 'Refresh',
                icon: 'icon-refresh',
                ngClick: "refresh()",
                class: 'btn-success btn-small',
                awToolTip: 'Refresh the page',
                mode: 'all'
                },
            edit: {
                label: 'Edit',
                icon: 'icon-edit',
                ngClick: "jobDetails()",
                class: 'btn-success btn-small',
                awToolTip: 'Edit job details',
                mode: 'all'
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                ngClick: "jobEvents()",
                class: 'btn-info btn-small',
                awToolTip: 'View job events',
                mode: 'all',             
                }
            },

        fieldActions: {
            }

        });
