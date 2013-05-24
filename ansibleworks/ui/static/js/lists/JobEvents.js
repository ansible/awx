/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Jobs.js 
 *  List view object for Team data model.
 *
 *
 */
angular.module('JobEventsListDefinition', [])
    .value(
    'JobEventList', {
        
        name: 'jobevents',
        iterator: 'jobevent',
        editTitle: 'Job Events',
        index: false,
        hover: true,
        
        fields: {
            id: {
                label: 'Event ID',
                key: true,
                desc: true,
                searchType: 'int'   
                },
            event: {
                label: 'Event',
                link: true
                },
            created: {
                label: 'Creation Date',
                },
            host: {
                label: 'Host',
                ngClick: "viewHost(\{\{ jobevent.host \}\})",
                ngBind: 'jobevent.host_name',
                sourceModel: 'host',
                sourceField: 'name'
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                class: 'job-\{\{ jobevent.status \}\}',
                searchField: 'failed',
                searchType: 'boolean',
                searchOptions: [{ name: "success", value: 0 }, { name: "error", value: 1 }]
                }
            },
        
        actions: {
            refresh: {
                ngClick: "refresh()",
                icon: 'icon-refresh',
                label: 'Refresh',
                awToolTip: 'Refresh the page',
                class: 'btn-small btn-success',
                mode: 'all'
                },
            edit: {
                label: 'View',
                ngClick: "jobDetails()",
                icon: 'icon-edit',
                class: 'btn-small btn-success',
                awToolTip: 'View/Edit detail',
                mode: 'all'
                },
            summary: {
                label: 'Hosts',
                icon: 'icon-filter',
                ngClick: "jobSummary()",
                class: 'btn-info btn-small',
                awToolTip: 'View host summary',
                mode: 'all'
                }
            },

        fieldActions: {
            edit: {
                label: 'View',
                ngClick: "editJobEvent(\{\{ jobevent.id \}\})",
                icon: 'icon-edit',
                class: 'btn-small',
                awToolTip: 'View event detail',
                },
            }
        });
