import multiCredential from './multi-credential.directive';
import multiCredentialModal from './multi-credential-modal.directive';
import multiCredentialService from './multi-credential.service';

export default
    angular.module('multiCredential', [])
        .directive('multiCredential', multiCredential)
        .directive('multiCredentialModal', multiCredentialModal)
        .service('MultiCredentialService', multiCredentialService);
