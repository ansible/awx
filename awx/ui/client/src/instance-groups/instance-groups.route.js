import {templateUrl} from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';

export default {
    name: 'instanceGroups',
    url: '/instance_groups',
    searchPrefix: 'instance_group',
    ncyBreadcrumb: {
        label: N_('INSTANCE GROUPS')
    },
    params: {
        instance_group_search: {
            value: {
                page_size: '20',
                order_by: 'name'
            },
            dynamic: true
        }
    },
    data: {
        alwaysShowRefreshButton: true,
    },
    views: {
        '@': {
            templateUrl: templateUrl('./instance-groups/instance-groups'),
        },
        'list@instanceGroups': {
            templateUrl: templateUrl('./instance-groups/list/instance-groups-list'),
            controller: 'InstanceGroupsList'

        }
    },
    resolve: {
        Dataset: ['InstanceGroupList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
