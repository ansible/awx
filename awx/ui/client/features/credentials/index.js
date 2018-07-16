import LegacyCredentials from './legacy.credentials';
import AddController from './add-credentials.controller';
import EditController from './edit-credentials.controller';
import CredentialsStrings from './credentials.strings';

const MODULE_NAME = 'at.features.credentials';

const addEditTemplate = require('~features/credentials/add-edit-credentials.view.html');

function CredentialsResolve (
    $q,
    $stateParams,
    Me,
    Credential,
    CredentialType,
    Organization,
    ProcessErrors,
    strings
) {
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
            dependents.isOrgCredAdmin = dependents.organization.then((org) => org.search({ role_level: 'credential_admin_role' }));

            return $q.all(dependents)
                .then(related => {
                    models.credentialType = related.credentialType;
                    models.organization = related.organization;
                    models.isOrgCredAdmin = related.isOrgCredAdmin;

                    return models;
                });
        }).catch(({ data, status, config }) => {
            ProcessErrors(null, data, status, null, {
                hdr: strings.get('error.HEADER'),
                msg: strings.get('error.CALL', { path: `${config.url}`, status })
            });
            return $q.reject();
        });
}

CredentialsResolve.$inject = [
    '$q',
    '$stateParams',
    'MeModel',
    'CredentialModel',
    'CredentialTypeModel',
    'OrganizationModel',
    'ProcessErrors',
    'CredentialsStrings'
];

function CredentialsRun ($stateExtender, legacy, strings) {
    $stateExtender.addState({
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

    $stateExtender.addState({
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

    $stateExtender.addState(legacy.getStateConfiguration('list'));
    $stateExtender.addState(legacy.getStateConfiguration('edit-permissions'));
    $stateExtender.addState(legacy.getStateConfiguration('add-permissions'));
    $stateExtender.addState(legacy.getStateConfiguration('add-organization'));
    $stateExtender.addState(legacy.getStateConfiguration('edit-organization'));
    $stateExtender.addState(legacy.getStateConfiguration('add-credential-type'));
    $stateExtender.addState(legacy.getStateConfiguration('edit-credential-type'));
}

CredentialsRun.$inject = [
    '$stateExtender',
    'LegacyCredentialsService',
    'CredentialsStrings'
];

angular
    .module(MODULE_NAME, [])
    .controller('AddController', AddController)
    .controller('EditController', EditController)
    .service('LegacyCredentialsService', LegacyCredentials)
    .service('CredentialsStrings', CredentialsStrings)
    .run(CredentialsRun);

export default MODULE_NAME;
