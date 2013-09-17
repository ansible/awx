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
        
        navigationLinks: {
            details: {
                href: "/#/jobs/{{ job_id }}",
                label: 'Details',
                icon: 'icon-zoom-in',
                ngShow: "job_id !== null"
                },
            events: {
                href: "/#/jobs/{{ job_id }}/job_events",
                label: 'Events',
                icon: 'icon-list-ul',
                ngShow: "job_id !== null"
                }
            },

        fields: {
            id: {
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
                ngClick:"showEvents('\{\{ jobhost.summary_fields.host.name \}\}','\{\{ jobhost.related.job \}\}')"
                },
            status: {
                label: 'Status',
                icon: 'icon-circle',
                "class": 'job-\{\{ jobhost.status \}\}',
                searchField: 'failed',
                searchType: 'boolean',
                searchOptions: [{ name: "success", value: 0 }, { name: "error", value: 1 }]
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
                awRefresh: true,
                ngShow: "host_id == null && (job_status == 'pending' || job_status == 'waiting' || job_status == 'running')",
                mode: 'all'
                },
            help: {
                awPopOver: "<dl>\n<dt>Success</dt><dd>Tasks successfully executed on the host.</dd>\n" +
                    "<dt>Changed</dt><dd>Actions taken on the host.</dd>\n" +
                    "<dt>Failure</dt><dd>Tasks that failed on the host.</dd>\n" +
                    "<dt>Unreachable</dt><dd>Times the ansible server could not reach the host.</dd>\n" +
                    "<dt>Skipped</dt><dd>Tasks bypassed and not performed on the host due to prior task failure or the host being unreachable.</dd>\n" +
                    "</dl>\n",
                dataPlacement: 'left',
                dataContainer: "body",
                icon: "icon-question-sign",
                mode: 'all',
                'class': 'btn-info btn-xs btn-help pull-right',
                awToolTip: 'Click for help',
                dataTitle: 'Job Host Summary',
                id: 'jobhost-help-button',
                iconSize: 'large'
                }
            },

        fieldActions: {
            }

        });
