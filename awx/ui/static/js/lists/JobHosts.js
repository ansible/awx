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
        indexShow: 'host_id == null',
        hover: true,
        
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
                label: 'Refresh',
                icon: 'icon-refresh',
                ngClick: "refresh()",
                "class": 'btn-primary btn-sm',
                awToolTip: 'Refresh the page',
                mode: 'all'
                },
            edit: {
                label: 'Details',
                icon: 'icon-edit',
                ngClick: "jobDetails()",
                ngShow: 'job_id !== null',
                "class": 'btn btn-default btn-sm',
                awToolTip: 'Edit job details',
                mode: 'all'
                },
            events: {
                label: 'Events',
                icon: 'icon-list-ul',
                ngClick: "jobEvents()",
                ngShow: 'job_id !== null',
                "class": 'btn btn-default btn-sm',
                awToolTip: 'View job events',
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
