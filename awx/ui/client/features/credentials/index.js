import LegacyCredentials from './legacy.credentials';
import AddController from './add-credentials.controller.js';
import EditController from './edit-credentials.controller.js';
import { N_ } from '../../src/i18n';

function CredentialsResolve ($q, $stateParams, Me, Credential, CredentialType) {
    let id = $stateParams.credential_id;

    let promises = {
        me: new Me('get'),
        credentialType: new CredentialType('get')
    };

    if (id) {
        promises.credential = new Credential(['get', 'options'], [id, id]);
    } else {
        promises.credential = new Credential('options');
    }

    return $q.all(promises);
}

CredentialsResolve.$inject = [
    '$q',
    '$stateParams',
    'MeModel',
    'CredentialModel',
    'CredentialTypeModel'
];

function CredentialsConfig ($stateExtenderProvider, legacyProvider, pathProvider) {
    let path = pathProvider.$get();
    let stateExtender = $stateExtenderProvider.$get();
    let legacy = legacyProvider.$get();

    stateExtender.addState({
        name: 'credentials.add',
        route: '/add',
        ncyBreadcrumb: {
            label: N_('CREATE CREDENTIALS')
        },
        views: {
            'add@credentials': {
                templateUrl: path.getViewPath('credentials/add-edit-credentials'),
                controller: AddController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: CredentialsResolve
        }
    });

    stateExtender.addState({
        name: 'credentials.edit',
        route: '/:credential_id',
        ncyBreadcrumb: {
            label: N_('EDIT')
        },
        views: {
            'edit@credentials': {
                templateUrl: path.getViewPath('credentials/add-edit-credentials'),
                controller: EditController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: CredentialsResolve
        }
    });

    stateExtender.addState(legacy.getStateConfiguration('list'));
    stateExtender.addState(legacy.getStateConfiguration('edit-permissions'));
    stateExtender.addState(legacy.getStateConfiguration('add-permissions'));
    stateExtender.addState(legacy.getStateConfiguration('add-organization'));
}

CredentialsConfig.$inject = [
    '$stateExtenderProvider',
    'LegacyCredentialsServiceProvider',
    'PathServiceProvider'
];

angular
    .module('at.features.credentials', [])
    .config(CredentialsConfig)
    .controller('AddController', AddController)
    .controller('EditController', EditController)
    .service('LegacyCredentialsService', LegacyCredentials);
