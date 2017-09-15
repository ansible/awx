import LegacyCredentials from './legacy.credentials';
import AddController from './add-credentials.controller';
import EditController from './edit-credentials.controller';
import CredentialsStrings from './credentials.strings';

const addEditTemplate = require('~features/credentials/add-edit-credentials.view.html');

function CredentialsResolve ($q, $stateParams, Me, Credential, CredentialType, Organization) {
    const id = $stateParams.credential_id;

    const promises = {
        me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
    };

    if (!id) {
        promises.credential = new Credential('options');
        promises.credentialType = new CredentialType();
        promises.organization = new Organization();

        return $q.all(promises);
    }

    promises.credential = new Credential(['get', 'options'], [id, id]);

    return $q.all(promises)
        .then(models => {
            const typeId = models.credential.get('credential_type');
            const orgId = models.credential.get('organization');

            const dependents = {
                credentialType: new CredentialType('get', typeId),
                organization: new Organization('get', orgId)
            };

            return $q.all(dependents)
                .then(related => {
                    models.credentialType = related.credentialType;
                    models.organization = related.organization;

                    return models;
                });
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

function CredentialsConfig ($stateExtenderProvider, legacyProvider, stringProvider) {
    const stateExtender = $stateExtenderProvider.$get();
    const legacy = legacyProvider.$get();
    const strings = stringProvider.$get();

    stateExtender.addState({
        name: 'credentials.add',
        route: '/add',
        ncyBreadcrumb: {
            label: strings.get('state.ADD_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'credential'
        },
        views: {
            'add@credentials': {
                templateUrl: addEditTemplate,
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
        data: {
            activityStream: true,
            activityStreamTarget: 'credential',
            activityStreamId: 'credential_id'
        },
        views: {
            'edit@credentials': {
                templateUrl: addEditTemplate,
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
    'CredentialsStringsProvider'
];

angular
    .module('at.features.credentials', [])
    .config(CredentialsConfig)
    .controller('AddController', AddController)
    .controller('EditController', EditController)
    .service('LegacyCredentialsService', LegacyCredentials)
    .service('CredentialsStrings', CredentialsStrings);
