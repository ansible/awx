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
        editTitle: 'All summaries',
        index: true,
        hover: true,
        
        navigationLinks: {
            ngHide: 'host_id !== null',
            details: {
                href: "/#/jobs/{{ job_id }}",
                label: 'Status',
                icon: 'icon-zoom-in',
                ngShow: "job_id !== null"
                },
            hosts: {
                href: "/#/jobs/{{ job_id }}/job_host_summaries",
                label: 'Summary',
                active: true,
                icon: 'icon-laptop'
                },
            events: {
                href: "/#/jobs/{{ job_id }}/job_events",
                label: 'Events',
                icon: 'icon-list-ul'
                }
            },

        fields: {
            job: {
                label: 'Job ID',
                ngClick: "showJob(\{\{ jobhost.job \}\})",
                columnShow: 'host_id !== null',
                key: true,
                desc: true
                },
            host: {
                label: 'Host',
                key: true,
                sourceModel: 'host',
                sourceField: 'name',
                ngBind: 'jobhost.host_name',
                ngHref: "\{\{ jobhost.hostLinkTo \}\}"
                },
            status: {
                label: 'Status',
                badgeNgHref: "\{\{ jobhost.statusLinkTo \}\}", 
                badgeIcon: 'icon-job-\{\{ jobhost.status \}\}',
                badgePlacement: 'left',
                badgeToolTip: "\{\{ jobhost.statusBadgeToolTip \}\}",
                badgeTipPlacement: 'top',
                ngHref: "\{\{ jobhost.statusLinkTo \}\}",
                awToolTip: "\{\{ jobhost.statusBadgeToolTip \}\}",
                dataPlacement: 'top',
                searchField: 'failed',
                searchType: 'boolean',
                searchOptions: [{ name: "success", value: 0 }, { name: "error", value: 1 }]
                },
            failed: {
                label: 'Job failed?',
                searchSingleValue: true,
                searchType: 'boolean',
                searchValue: 'true',
                searchOnly: true,
                nosort: true
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
                searchable: true,
                searchLabel: 'Contains failed events?',
                searchType: 'gtzero'
                },
            dark: {
                label: 'Unreachable',
                searchable: true,
                searchType: 'gtzero',
                searchLabel: 'Contains unreachable hosts?'
                },
            skipped: {
                label: 'Skipped',
                searchable: false
                }
            },
        
        actions: {
            help: {
                awPopOver: "<dl>\n<dt>Success</dt><dd>Tasks successfully executed on the host.</dd>\n" +
                    "<dt>Changed</dt><dd>Actions taken on the host.</dd>\n" +
                    "<dt>Failure</dt><dd>Tasks that failed on the host.</dd>\n" +
                    "<dt>Unreachable</dt><dd>Times the ansible server could not reach the host.</dd>\n" +
                    "<dt>Skipped</dt><dd>Tasks bypassed and not performed on the host due to prior task failure or the host being unreachable.</dd>\n" +
                    "</dl>\n",
                dataPlacement: 'top',
                dataContainer: "body",
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-info btn-xs btn-help',
                awToolTip: 'Click for help',
                dataTitle: 'Job Host Summary',
                id: 'jobhost-help-button',
                iconSize: 'large'
                },
            refresh: {
                awRefresh: true,
                ngShow: "host_id == null && (job_status == 'pending' || job_status == 'waiting' || job_status == 'running')",
                mode: 'all'
                }
            },

        fieldActions: {
            }

        });
