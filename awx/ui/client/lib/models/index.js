import Base from './Base';
import CredentialType from './CredentialType';

function config ($resourceProvider) {
    $resourceProvider.defaults.stripTrailingSlashes = false;
}

config.$inject = ['$resourceProvider'];

angular
    .module('at.lib.models', [])
    .config(config)
    .service('BaseModel', Base)
    .service('CredentialType', CredentialType);

