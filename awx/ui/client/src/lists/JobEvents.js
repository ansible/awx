/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('JobEventsListDefinition', [])
    .factory('JobEventList', ['i18n', function(i18n) {
    return {

        name: 'jobevents',
        iterator: 'jobevent',
        editTitle: i18n._('JOB EVENTS'),
        index: false,
        hover: true,
        "class": "condensed",
        hasChildren: true,
        filterBy: '{ show: true }',

        navigationLinks: {
            //details: {
            //    href: '/#/jobs/{{ job_id }}',
            //    label: 'Status',
            //    icon: 'icon-zoom-in',
            //    ngShow: 'job_id !== null'
            //},
            events: {
                href: '/#/job_events/{{ job_id }}',
                label: i18n._('Events'),
                active: true,
                icon: 'icon-list-ul'
            },
            hosts: {
                href: '/#/job_host_summaries/{{ job_id }}',
                label: i18n._('Host Summary'),
                icon: 'icon-laptop'
            }
        },

        fields: {
            created: {
                label: i18n._('Created On'),
                columnClass: 'col-lg-1 col-md-1 hidden-sm hidden-xs',
                key: true,
                nosort: true,
                noLink: true
            },
            status: {
                label: i18n._('Status'),
                showValue: false,
                columnClass: 'col-sm-1 col-xs-2 text-center',
                nosort: true,
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
                label: i18n._('Event'),
                hasChildren: true,
                ngClick: 'toggleChildren(jobevent.id, jobevent.related.children)',
                nosort: true,
                ngClass: '{{ jobevent.class }}',
                appendHTML: 'jobevent.event_detail'
            },
            host: {
                label: i18n._('Host'),
                ngBind: 'jobevent.summary_fields.host.name',
                ngHref: '{{ jobevent.hostLink }}',
                nosort: true,
                id: 'job-event-host-header',
                'class': 'break',
                columnClass: 'col-lg-2 hidden-sm hidden-xs'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                awToolTip: 'Refresh the page',
                ngClick: 'refresh()',
                actionClass: 'btn List-buttonDefault',
                buttonContent: i18n._('REFRESH')
            }
        },

        fieldActions: {

            columnClass: 'col-sm-1 col-xs-2',

            view: {
                label: i18n._('View'),
                ngClick: 'viewJobEvent(jobevent.id)',
                awToolTip: i18n._('View event details'),
                dataPlacement: 'top'
            }
        }
    };}]);
