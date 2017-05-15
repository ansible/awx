import Base from './Base';
import Credential from './Credential';
import CredentialType from './CredentialType';

function config ($resourceProvider) {
    $resourceProvider.defaults.stripTrailingSlashes = false;
}

config.$inject = ['$resourceProvider'];

angular
    .module('at.lib.models', [])
    .config(config)
    .service('BaseModel', Base)
    .service('CredentialModel', Credential)
    .service('CredentialTypeModel', CredentialType);

