import { N_ } from '../../i18n';

export default {
    name: 'instanceGroups.instances.jobs',
    url: '/jobs',
    searchPrefix: 'job',
    ncyBreadcrumb: {
        parent: 'instanceGroups.instances.list',
        label: N_('JOBS')
    },
    params: {
        job_search: {
            value: {
                page_size: '20',
                order_by: '-finished',
                not__launch_type: 'sync'
            },
            dynamic: true
        },
        instance_group_id: null
    },
    views: {
        'list@instanceGroups.instances': {
            templateProvider: function(JobsList, generateList) {
                let html = generateList.build({
                    list: JobsList
                });
                return html;
            },
            controller: 'JobsListController'
        }
    },
    resolve: {
        Dataset: ['JobsList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('instance_groups')}${$stateParams.instance_group_id}/jobs`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
