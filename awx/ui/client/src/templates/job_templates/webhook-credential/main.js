import webhookCredential from './webhook-credential.directive';
import webhookCredentialModal from './webhook-credential-modal.directive';
import webhookCredentialService from './webhook-credential.service';

export default
    angular.module('webhookCredential', [])
        .directive('webhookCredential', webhookCredential)
        .directive('webhookCredentialModal', webhookCredentialModal)
        .service('WebhookCredentialService', webhookCredentialService);
