import multiCredential from './multi-credential.directive';
import multiCredentialModal from './multi-credential-modal.directive';

export default
    angular.module('multiCredential', [])
        .directive('multiCredential', multiCredential)
        .directive('multiCredentialModal', multiCredentialModal);
