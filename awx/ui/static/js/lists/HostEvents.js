/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  HostEvents.js
 *  Host summary event viewer dialog.
 *
 */

'use strict';

angular.module('HostEventsListDefinition', [])
    .value('HostEventList', {

        name: 'host_events',
        iterator: 'host_event',
        editTitle: 'Host Events',
        index: false,
        hover: true,

        fields: {
            status: {
                label: 'Status',
                columnClass: 'col-md-2',

            },
            play: {
                label: 'Play',
                columnClass: 'col-md-3',
                key: true,
                nosort: true,
                searchable: false,
                noLink: true
            },
            status: {
                label: 'Status',
                showValue: false,
                columnClass: 'col-sm-1 col-xs-2 text-center',
                searchField: 'failed',
                searchType: 'boolean',
                searchOptions: [{
                    name: 'success',
                    value: 0
                }, {
                    name: 'error',
                    value: 1
                }],
                nosort: true,
                searchable: false,
                ngClick: 'viewJobEvent(jobevent.id)',
                awToolTip: '{{ jobevent.statusBadgeToolTip }}',
                dataPlacement: 'top',
                badgeIcon: 'fa icon-job-{{ jobevent.status }}',
                badgePlacement: 'left',
                badgeToolTip: '{{ jobevent.statusBadgeToolTip }}',
                badgeTipPlacement: 'top',
                badgeNgClick: 'viewJobEvent(jobevent.id)'
            },
            event_display: {
                label: 'Event',
                hasChildren: true,
                ngClick: 'toggleChildren(jobevent.id, jobevent.related.children)',
                nosort: true,
                searchable: false,
                ngClass: '{{ jobevent.class }}',
                appendHTML: 'jobevent.event_detail'
            },
            host: {
                label: 'Host',
                ngBind: 'jobevent.summary_fields.host.name',
                ngHref: '{{ jobevent.hostLink }}',
                searchField: 'hosts__name',
                nosort: true,
                searchOnly: false,
                id: 'job-event-host-header',
                'class': 'break',
                columnClass: 'col-lg-2 hidden-sm hidden-xs'
            }
        },

        actions: { },

    });