import LegacyCredentials from './legacy.credentials';
import AddController from './add-credentials.controller';
import EditController from './edit-credentials.controller';
import CredentialsStrings from './credentials.strings'

function CredentialsResolve ($q, $stateParams, Me, Credential, CredentialType, Organization) {
    let id = $stateParams.credential_id;

    let promises = {
        me: new Me('get'),
        credentialType: new CredentialType('get'),
        organization: new Organization('get')
    };

    if (!id) {
        promises.credential = new Credential('options');

        return $q.all(promises)
    }

    promises.credential = new Credential(['get', 'options'], [id, id]);

    return $q.all(promises)
        .then(models => {
            let credentialTypeId = models.credential.get('credential_type');
            models.selectedCredentialType = models.credentialType.graft(credentialTypeId);

            return models;
        });
}

CredentialsResolve.$inject = [
    '$q',
    '$stateParams',
    'MeModel',
    'CredentialModel',
    'CredentialTypeModel',
    'OrganizationModel'
];

function CredentialsConfig ($stateExtenderProvider, legacyProvider, pathProvider, stringProvider) {
    let path = pathProvider.$get();
    let stateExtender = $stateExtenderProvider.$get();
    let legacy = legacyProvider.$get();
    let strings = stringProvider.$get();

    stateExtender.addState({
        name: 'credentials.add',
        route: '/add',
        ncyBreadcrumb: {
            label: strings.get('state.ADD_BREADCRUMB_LABEL')
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
            label: strings.get('state.EDIT_BREADCRUMB_LABEL')
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
    stateExtender.addState(legacy.getStateConfiguration('edit-organization'));
    stateExtender.addState(legacy.getStateConfiguration('add-credential-type'));
    stateExtender.addState(legacy.getStateConfiguration('edit-credential-type'));
}

CredentialsConfig.$inject = [
    '$stateExtenderProvider',
    'LegacyCredentialsServiceProvider',
    'PathServiceProvider',
    'CredentialsStringsProvider'
];

angular
    .module('at.features.credentials', [])
    .config(CredentialsConfig)
    .controller('AddController', AddController)
    .controller('EditController', EditController)
    .service('LegacyCredentialsService', LegacyCredentials)
    .service('CredentialsStrings', CredentialsStrings);
