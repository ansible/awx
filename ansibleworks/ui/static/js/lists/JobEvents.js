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
        hasChildren: true,
        
        fields: {
            created: {
                label: 'Creation Date',
                key: true,
                nosort: true
                },
            event_display: {
                label: 'Event',
                hasChildren: true,
                link: true,
                nosort: true
                },
            host: {
                label: 'Host',
                ngClick: "viewHost(\{\{ jobevent.host \}\})",
                ngBind: 'jobevent.summary_fields.host.name',
                searchField: 'hosts__name',
                nosort: true,
                id: 'job-event-host-header'
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                "class": 'job-\{\{ jobevent.status \}\}',
                searchField: 'failed',
                searchType: 'boolean',
                searchOptions: [{ name: "success", value: 0 }, { name: "error", value: 1 }],
                nosort: true
                }
            },
        
        actions: {
            refresh: {
                ngClick: "refresh()",
                icon: 'icon-refresh',
                label: 'Refresh',
                awToolTip: 'Refresh the page',
                "class": 'btn-small btn-success',
                mode: 'all'
                },
            edit: {
                label: 'Edit',
                ngClick: "jobDetails()",
                icon: 'icon-edit',
                "class": 'btn-small btn-success',
                awToolTip: 'Edit job details',
                mode: 'all'
                },
            summary: {
                label: 'Hosts',
                icon: 'icon-th-large',
                ngClick: "jobSummary()",
                "class": 'btn-info btn-small',
                awToolTip: 'View host summary',
                mode: 'all'
                }
            },

        fieldActions: {
            edit: {
                label: 'View',
                ngClick: "editJobEvent(\{\{ jobevent.id \}\})",
                icon: 'icon-zoom-in',
                "class": 'btn-small',
                awToolTip: 'View event details'
                }
            }
        });
