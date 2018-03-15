import { N_ } from '../i18n';

import ListController from './users-tokens-list.controller';

const listTemplate = require('~src/users/users-tokens-list.partial.html');

export default {
    url: "/tokens",
    name: 'users.edit.tokens',
    params: {
    },
    ncyBreadcrumb: {
        label: N_("TOKENS")
    },
    views: {
        'related': {
            templateUrl: listTemplate,
            controller: ListController,
            controllerAs: 'vm'
        }
    },
    searchPrefix: 'token',
    params: {
        token_search: {
            value: {
                page_size: 5,
                order_by: 'application'
            }
        }
    },
    resolve: {
        Dataset: [
            '$stateParams',
            'Wait',
            'GetBasePath',
            'QuerySet',
            ($stateParams, Wait, GetBasePath, qs) => {
                const searchParam = $stateParams.token_search;
                const searchPath = GetBasePath('users') + $stateParams.user_id + '/tokens';
                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => {
                        Wait('stop');
                    });
            }
        ],
    }
};
