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

            },

        fieldActions: {
            }

        });
