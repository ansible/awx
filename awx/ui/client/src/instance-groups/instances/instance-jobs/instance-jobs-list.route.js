import { N_ } from '../../../i18n';

export default {
    name: 'instanceGroups.instances.list.job.list',
    url: '/jobs',
    searchPrefix: 'instance_job',
    ncyBreadcrumb: {
        parent: 'instanceGroups.instances.list',
        label: N_('{{ breadcrumb.instance_name }}')
    },
    params: {
        instance_job_search: {
            value: {
                page_size: '20',
                order_by: '-finished',
                not__launch_type: 'sync'
            },
            dynamic: true
        }
    },
    views: {
        'list@instanceGroups.instances.list.job': {
            templateProvider: function(InstanceJobsList, generateList) {
                let html = generateList.build({
                    list: InstanceJobsList
                });
                return html;
            },
        controller: 'InstanceJobsController'
        }
    },

    resolve: {
        Dataset: ['InstanceJobsList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('instances')}${$stateParams.instance_id}/jobs`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
    }
};
