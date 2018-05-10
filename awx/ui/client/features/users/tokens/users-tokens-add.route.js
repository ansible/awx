import { N_ } from '../../../src/i18n';
import AddController from './users-tokens-add.controller';

const addTemplate = require('~features/users/tokens/users-tokens-add.partial.html');

function TokensDetailResolve ($q, Application) {
    const promises = {};

    promises.application = new Application('options');

    return $q.all(promises);
}

TokensDetailResolve.$inject = [
    '$q',
    'ApplicationModel'
];

export default {
    url: '/add-token',
    name: 'users.edit.tokens.add',
    params: {
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'o_auth2_access_token',
        noActivityStreamID: true
    },
    ncyBreadcrumb: {
        label: N_('CREATE TOKEN')
    },
    views: {
        'preFormView@users.edit': {
            templateUrl: addTemplate,
            controller: AddController,
            controllerAs: 'vm'
        }
    },
    resolve: {
        resolvedModels: TokensDetailResolve
    }
};
