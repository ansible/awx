import { N_ } from '../i18n';
import AddController from './users-tokens-add.controller';

const addTemplate = require('~src/users/users-tokens-add.partial.html');

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
    url: "/add-token",
    name: 'users.edit.tokens.add',
    params: {
    },
    ncyBreadcrumb: {
        label: N_("ADD TOKEN")
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
