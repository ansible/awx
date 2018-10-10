import { N_ } from '../../../src/i18n';
import AddController from './users-tokens-add.controller';

const addTemplate = require('~features/users/tokens/users-tokens-add.partial.html');

function TokensDetailResolve ($q, Application, Token, User) {
    const promises = {};

    promises.application = new Application('options');
    promises.token = new Token('options');
    promises.user = new User('options');

    return $q.all(promises);
}

TokensDetailResolve.$inject = [
    '$q',
    'ApplicationModel',
    'TokenModel',
    'UserModel'
];

function isMeResolve ($rootScope, $stateParams, $state) {
    // The user should not be able to add tokens for users other than
    // themselves. Adding this redirect so that a user is not able to
    // visit the add-token URL directly for a different user.
    if (_.has($stateParams, 'user_id') && Number($stateParams.user_id) !== $rootScope.current_user.id) {
        $state.go('users');
    }
}

isMeResolve.$inject = [
    '$rootScope',
    '$stateParams',
    '$state'
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
        'preFormView@users': {
            templateUrl: addTemplate,
            controller: AddController,
            controllerAs: 'vm'
        }
    },
    resolve: {
        resolvedModels: TokensDetailResolve,
        isMe: isMeResolve
    }
};
