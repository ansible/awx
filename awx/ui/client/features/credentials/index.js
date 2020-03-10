import LegacyCredentials from './legacy.credentials';
import AddEditController from './add-edit-credentials.controller';
import CredentialsStrings from './credentials.strings';
import InputSourceLookupComponent from './input-source-lookup.component';
import ExternalTestModalComponent from './external-test-modal.component';

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
    strings,
    Rest,
    GetBasePath,
) {
    const id = $stateParams.credential_id;

    const promises = {
        me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
    };

    if (!id) {
        promises.credential = new Credential('options');
        promises.credentialType = new CredentialType();
        promises.organization = new Organization();
        promises.sourceCredentials = $q.resolve({ data: { count: 0, results: [] } });

        return $q.all(promises);
    }

    promises.credential = new Credential(['get', 'options'], [id, id]);

    return $q.all(promises)
        .then(models => {
            const typeId = models.credential.get('credential_type');

            Rest.setUrl(GetBasePath('credentials'));
            const params = { target_input_sources__target_credential: id };
            const sourceCredentialsPromise = Rest.get({ params });

            const dependents = {
                credentialType: new CredentialType('get', typeId),
                organization: new Organization('get', {
                    resource: models.credential.get('summary_fields.organization')
                }),
                credentialInputSources: models.credential.extend('GET', 'input_sources'),
                sourceCredentials: sourceCredentialsPromise
            };

            dependents.isOrgCredAdmin = dependents.organization.then((org) => org.search({ role_level: 'credential_admin_role' }));

            return $q.all(dependents)
                .then(related => {
                    models.credentialType = related.credentialType;
                    models.organization = related.organization;
                    models.sourceCredentials = related.sourceCredentials;

                    const isOrgAdmin = _.some(models.me.get('related.admin_of_organizations.results'), (org) => org.id === models.organization.get('id'));
                    const isSuperuser = models.me.get('is_superuser');
                    const isCurrentAuthor = Boolean(models.credential.get('summary_fields.created_by.id') === models.me.get('id'));

                    models.isOrgEditableByUser = (isSuperuser || isOrgAdmin
                        || related.isOrgCredAdmin
                        || (models.credential.get('organization') === null && isCurrentAuthor));

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
    'CredentialsStrings',
    'Rest',
    'GetBasePath',
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
                controller: AddEditController,
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
                controller: AddEditController,
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
    .controller('AddEditController', AddEditController)
    .service('LegacyCredentialsService', LegacyCredentials)
    .service('CredentialsStrings', CredentialsStrings)
    .component('atInputSourceLookup', InputSourceLookupComponent)
    .component('atExternalCredentialTest', ExternalTestModalComponent)
    .run(CredentialsRun);

export default MODULE_NAME;
