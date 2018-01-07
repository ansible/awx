/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
const templatePath = 'templates/job_templates/multi-credential/multi-credential';

function MultiCredential ($compile, templateUrl) {
    return {
        templateUrl: templateUrl(templatePath),
        require: ['multiCredential'],
        restrict: 'E',
        controllerAs: 'vm',
        scope: {
            selectedCredentials: '=',
            prompt: '=',
            credentialNotPresent: '=',
            fieldIsDisabled: '=',
            credentialTypes: '=',
        },
        link: (scope, element, attrs, controllers) => {
            const [controller] = controllers;

            scope.openModal = () => {
                const containerElement = $('#content-container');
                const templateFunction = $compile(`
                    <multi-credential-modal
                        credential-types="credentialTypes"
                        selected-credentials="selectedCredentials">
                    </multi-credential-modal>`);
                containerElement.append(templateFunction(scope));
            };

            controller.init(scope);
        },
        controller: multiCredentialController,
    };
}

function multiCredentialController (MultiCredentialService) {
    const vm = this;
    const { createTag } = MultiCredentialService;

    let scope;

    vm.init = _scope_ => {
        scope = _scope_;
        scope.$watchCollection('selectedCredentials', onSelectedCredentialsChanged);
    };

    function onSelectedCredentialsChanged (oldValues, newValues) {
        if (oldValues !== newValues) {
            scope.fieldDirty = (scope.prompt && scope.selectedCredentials.length > 0);
            scope.tags = scope.selectedCredentials.map(c => createTag(c, scope.credentialTypes));
        }
    }

    vm.deselectCredential = ({ id }) => {
        const index = scope.selectedCredentials.map(c => c.id).indexOf(id);

        if (index > -1) {
            scope.selectedCredentials.splice(index, 1);
        }
    };
}

MultiCredential.$inject = ['$compile', 'templateUrl'];
multiCredentialController.$inject = ['MultiCredentialService'];

export default MultiCredential;
