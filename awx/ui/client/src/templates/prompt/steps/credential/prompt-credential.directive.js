/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import promptCredentialController from './prompt-credential.controller';

export default [ 'templateUrl', '$compile', 'generateList', 'i18n',
    (templateUrl, $compile, GenerateList, i18n) => {
    return {
        scope: {
          promptData: '=',
          credentialPasswordsForm: '=',
          preventCredsWithPasswords: '<',
          readOnlyPrompts: '<'
        },
        templateUrl: templateUrl('templates/prompt/steps/credential/prompt-credential'),
        controller: promptCredentialController,
        controllerAs: 'vm',
        require: ['^^prompt', 'promptCredential'],
        restrict: 'E',
        replace: true,
        transclude: true,
        link: (scope, el, attrs, controllers) => {

            const launchController = controllers[0];
            const promptCredentialController = controllers[1];

            scope.generateCredentialList = (credKind) => {
                let inputType = (credKind && scope.promptData.prompts.credentials.credentialTypes[credKind] === "vault") ? null : 'radio';
                let list = _.cloneDeep(scope.list);

                if(credKind && scope.promptData.prompts.credentials.credentialTypes[credKind] === "vault") {
                    list.fields.name.modalColumnClass = 'col-md-6';
                    list.fields.info = {
                        label: i18n._('Vault ID'),
                        ngBind: 'credential.inputs.vault_id',
                        key: false,
                        nosort: true,
                        modalColumnClass: 'col-md-6',
                        infoHeaderClass: '',
                        dataPlacement: 'top',
                    };
                }

                list.disableRow = "{{ readOnlyPrompts }}";
                list.disableRowValue = "readOnlyPrompts";

                let html = GenerateList.build({
                    list: list,
                    input_type: inputType,
                    mode: 'lookup'
                });
                $('#prompt-credential').empty().append($compile(html)(scope));
            };

            promptCredentialController.init(scope, launchController);
        }
    };
}];
