import { N_ } from '../../../src/i18n';

import ListController from './users-tokens-list.controller';

const listTemplate = require('~features/users/tokens/users-tokens-list.partial.html');

function TokensListResolve ($q, Token) {
    const promises = {};

    promises.token = new Token('options');

    return $q.all(promises);
}

TokensListResolve.$inject = [
    '$q',
    'TokenModel',
];

export default {
    url: '/tokens',
    name: 'users.edit.tokens',
    ncyBreadcrumb: {
        label: N_('TOKENS')
    },
    views: {
        related: {
            templateUrl: listTemplate,
            controller: ListController,
            controllerAs: 'vm'
        }
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'o_auth2_access_token',
        noActivityStreamID: true
    },
    searchPrefix: 'token',
    params: {
        token_search: {
            value: {
                page_size: 10,
                order_by: 'application__name'
            }
        }
    },
    resolve: {
        resolvedModels: TokensListResolve,
        Dataset: [
            '$stateParams',
            'Wait',
            'GetBasePath',
            'QuerySet',
            ($stateParams, Wait, GetBasePath, qs) => {
                const searchParam = $stateParams.token_search;
                const searchPath = `${GetBasePath('users')}${$stateParams.user_id}/tokens`;
                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => {
                        Wait('stop');
                    });
            }
        ],
    }
};
