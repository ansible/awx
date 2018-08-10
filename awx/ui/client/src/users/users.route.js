import {templateUrl} from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';

export default {
    name: 'users',
    route: '/users',
    ncyBreadcrumb: {
        label: N_('USERS')
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'user'
    },
    params: {
        user_search: {
            value: {
                page_size: 20,
                order_by: 'username'
            }
        }
    },
    views: {
        '@': {
            templateUrl: templateUrl('users/users')
        },
        'list@users': {
            templateProvider: function(UserList, generateList) {
                let html = generateList.build({
                    list: UserList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                return html;
            },
            controller: 'UsersList'
        }
    },
    searchPrefix: 'user',
    resolve: {
        Dataset: ['UserList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        resolvedModels: ['MeModel', '$q',  function(Me, $q) {
            const promises= {
                me: new Me('get')
            };

            return $q.all(promises);
        }]
        
    }
};
