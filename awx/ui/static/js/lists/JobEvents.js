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
        filterBy: '\{ show: true \}',

        navigationLinks: {
            details: {
                href: "/#/jobs/{{ job_id }}",
                label: 'Job Details',
                icon: 'icon-zoom-in',
                ngShow: "job_id !== null"
                },
            hosts: {
                href: "/#/jobs/{{ job_id }}/job_host_summaries",
                label: 'Hosts',
                icon: 'icon-laptop'
                },
            events: {
                href: "/#/jobs/{{ job_id }}/job_events",
                label: 'Events',
                active: true,
                icon: 'icon-list-ul'
                }
            },
        
        fields: {
            created: {
                label: 'Created On',
                key: true,
                nosort: true,
                searchable: false,
                link: false
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                showValue: true,
                "class": 'job-\{\{ jobevent.status \}\}',
                searchField: 'failed',
                searchType: 'boolean',
                searchOptions: [{ name: "success", value: 0 }, { name: "error", value: 1 }],
                nosort: true,
                searchable: false
                },
            event_display: {
                label: 'Event',
                hasChildren: true,
                ngClick: "toggleChildren(\{\{ jobevent.id \}\}, '\{\{ jobevent.related.children \}\}')",
                nosort: true,
                searchable: false,
                ngClass: '\{\{ jobevent.class \}\}',
                appendHTML: 'jobevent.event_detail'
                },
            host: {
                label: 'Host',
                ngBind: 'jobevent.summary_fields.host.name',
                searchField: 'hosts__name',
                nosort: true,
                searchOnly: false,
                id: 'job-event-host-header',
                columnClass: 'hidden-sm'
                }
            },
        
        actions: {
            refresh: {
                awRefresh: true,
                ngShow: "job_status == 'pending' || job_status == 'waiting' || job_status == 'running'",
                mode: 'all'
                }
            },

        fieldActions: {
            edit: {
                label: 'View',
                ngClick: "viewJobEvent(\{\{ jobevent.id \}\})",
                icon: 'icon-zoom-in',
                "class": 'btn-default btn-xs',
                awToolTip: 'View event details'
                }
            }
        });
