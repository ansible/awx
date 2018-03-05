/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait', 'UserTokensFormObject',
    'ProcessErrors', 'GetBasePath', 'Alert',
    'GenerateForm', '$scope', '$state', 'CreateSelect2', 'GetChoices' 'i18n',
    function(
        Rest, Wait, UserTokensFormObject,
        ProcessErrors, GetBasePath, Alert,
        GenerateForm, $scope, $state, CreateSelect2, GetChoices i18n
    ) {

        var generator = GenerateForm,
            form = UserTokensFormObject;

        init();

        function init() {
            Rest.setUrl(GetBasePath('users') + '/authorized_tokens');
            Rest.options()
                .then(({data}) => {
                    if (!data.actions.POST) {
                        $state.go("^");
                        Alert('Permission Error', 'You do not have permission to add a token.', 'alert-info');
                    }
                });
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);
        }

        CreateSelect2({
            element: '#user_token_scope',
            multiple: false
        });

        // Save
        $scope.formSave = function() {
            // var params,
            //     v = $scope.notification_type.value;
            //
            // generator.clearApiErrors($scope);
            // params = {
            //     "name": $scope.name,
            //     "description": $scope.description,
            //     "organization": $scope.organization,
            //     "notification_type": v,
            //     "notification_configuration": {}
            // };
            //
            // function processValue(value, i, field) {
            //     if (field.type === 'textarea') {
            //         if (field.name === 'headers') {
            //             $scope[i] = JSON.parse($scope[i]);
            //         } else {
            //             $scope[i] = $scope[i].toString().split('\n');
            //         }
            //     }
            //     if (field.type === 'checkbox') {
            //         $scope[i] = Boolean($scope[i]);
            //     }
            //     if (field.type === 'number') {
            //         $scope[i] = Number($scope[i]);
            //     }
            //     if (i === "username" && $scope.notification_type.value === "email" && value === null) {
            //         $scope[i] = "";
            //     }
            //     if (field.type === 'sensitive' && value === null) {
            //         $scope[i] = "";
            //     }
            //     return $scope[i];
            // }
            //
            // params.notification_configuration = _.object(Object.keys(form.fields)
            //     .filter(i => (form.fields[i].ngShow && form.fields[i].ngShow.indexOf(v) > -1))
            //     .map(i => [i, processValue($scope[i], i, form.fields[i])]));
            //
            //     delete params.notification_configuration.email_options;
            //
            //     for(var j = 0; j < form.fields.email_options.options.length; j++) {
            //         if(form.fields.email_options.options[j].ngShow && form.fields.email_options.options[j].ngShow.indexOf(v) > -1) {
            //             params.notification_configuration[form.fields.email_options.options[j].value] = Boolean($scope[form.fields.email_options.options[j].value]);
            //         }
            //     }
            //
            // Wait('start');
            // Rest.setUrl(url);
            // Rest.post(params)
            //     .then(() => {
            //         $state.go('notifications', {}, { reload: true });
            //         Wait('stop');
            //     })
            //     .catch(({data, status}) => {
            //         ProcessErrors($scope, data, status, form, {
            //             hdr: 'Error!',
            //             msg: 'Failed to add new notifier. POST returned status: ' + status
            //         });
            //     });
        };

        $scope.formCancel = function() {
            $state.go('notifications');
        };

    }
];
