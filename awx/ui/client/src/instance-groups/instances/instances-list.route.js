import {templateUrl} from '../../shared/template-url/template-url.factory';
import { N_ } from '../../i18n';

export default {
    name: 'instanceGroups.instances.list',
    url: '/instances',
    searchPrefix: 'instance',
    ncyBreadcrumb: {
        parent: 'instanceGroups',
        label: N_('{{breadcrumb.instance_group_name}}')
    },
    params: {
        instance_search: {
            value: {
                page_size: '20',
                order_by: 'hostname'
            },
            dynamic: true
        }
    },
    views: {
        'list@instanceGroups.instances': {
            templateUrl: templateUrl('./instance-groups/instances/instances-list'),
            controller: 'InstanceListController'
        }
    },
    resolve: {
        Dataset: ['InstanceList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('instance_groups')}${$stateParams.instance_group_id}/instances`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
