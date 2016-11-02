/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', 'Rest', 'Wait', 'NotificationsFormObject',
    'ProcessErrors', 'GetBasePath', 'Empty', 'Alert',
    'GenerateForm', '$scope', '$state', 'CreateSelect2', 'GetChoices',
    'NotificationsTypeChange', 'ParseTypeChange',
    function(
        $rootScope, Rest, Wait, NotificationsFormObject,
        ProcessErrors, GetBasePath, Empty, Alert,
        GenerateForm, $scope, $state, CreateSelect2, GetChoices,
        NotificationsTypeChange, ParseTypeChange
    ) {

        var generator = GenerateForm,
            form = NotificationsFormObject,
            url = GetBasePath('notification_templates');

        init();

        function init() {
            Rest.setUrl(GetBasePath('projects'));
            Rest.options()
                .success(function(data) {
                    if (!data.actions.POST) {
                        $state.go("^");
                        Alert('Permission Error', 'You do not have permission to add a notification template.', 'alert-info');
                    }
                });
            // apply form definition's default field values
            GenerateForm.applyDefaults(form, $scope);

            GetChoices({
                scope: $scope,
                url: url,
                field: 'notification_type',
                variable: 'notification_type_options',
                callback: 'choicesReady'
            });
        }

        if ($scope.removeChoicesReady) {
            $scope.removeChoicesReady();
        }
        $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
            var i;
            for (i = 0; i < $scope.notification_type_options.length; i++) {
                if ($scope.notification_type_options[i].value === '') {
                    $scope.notification_type_options[i].value = "manual";
                    break;
                }
            }
            CreateSelect2({
                element: '#notification_template_notification_type',
                multiple: false
            });
        });

        $scope.$watch('headers', function validate_headers(str) {
            try {
                let headers = JSON.parse(str);
                if (_.isObject(headers) && !_.isArray(headers)) {
                    let valid = true;
                    for (let k in headers) {
                        if (_.isObject(headers[k])) {
                            valid = false;
                        }
                        if (headers[k] === null) {
                            valid = false;
                        }
                    }
                    $scope.notification_template_form.headers.$setValidity('json', valid);
                    return;
                }
            } catch (err) {}

            $scope.notification_template_form.headers.$setValidity('json', false);
        });

        $scope.typeChange = function() {
            for (var fld in form.fields) {
                if (form.fields[fld] && form.fields[fld].subForm) {
                    if (form.fields[fld].type === 'checkbox_group' && form.fields[fld].fields) {
                        // Need to loop across the groups fields to null them out
                        for (var i = 0; i < form.fields[fld].fields.length; i++) {
                            // Pull the name out of the object (array of objects)
                            var subFldName = form.fields[fld].fields[i].name;
                            $scope[subFldName] = null;
                            $scope.notification_template_form[subFldName].$setPristine();
                        }
                    } else {
                        $scope[fld] = null;
                        $scope.notification_template_form[fld].$setPristine();
                    }
                }
            }

            NotificationsTypeChange.getDetailFields($scope.notification_type.value).forEach(function(field) {
                $scope[field[0]] = field[1];
            });


            $scope.parse_type = 'json';
            if (!$scope.headers) {
                $scope.headers = "{\n}";
            }
            ParseTypeChange({
                scope: $scope,
                parse_variable: 'parse_type',
                variable: 'headers',
                field_id: 'notification_template_headers'
            });
        };

        // Save
        $scope.formSave = function() {
            var params,
                v = $scope.notification_type.value;

            generator.clearApiErrors($scope);
            params = {
                "name": $scope.name,
                "description": $scope.description,
                "organization": $scope.organization,
                "notification_type": v,
                "notification_configuration": {}
            };

            function processValue(value, i, field) {
                if (field.type === 'textarea') {
                    if (field.name === 'headers') {
                        $scope[i] = JSON.parse($scope[i]);
                    } else {
                        $scope[i] = $scope[i].toString().split('\n');
                    }
                }
                if (field.type === 'checkbox') {
                    $scope[i] = Boolean($scope[i]);
                }
                if (field.type === 'number') {
                    $scope[i] = Number($scope[i]);
                }
                if (field.name === "username" && $scope.notification_type.value === "email" && value === null) {
                    $scope[i] = "";
                }
                if (field.type === 'sensitive' && value === null) {
                    $scope[i] = "";
                }
                return $scope[i];
            }

            params.notification_configuration = _.object(Object.keys(form.fields)
                .filter(i => (form.fields[i].ngShow && form.fields[i].ngShow.indexOf(v) > -1))
                .map(i => [i, processValue($scope[i], i, form.fields[i])]));

            delete params.notification_configuration.checkbox_group;

            for (var j = 0; j < form.fields.checkbox_group.fields.length; j++) {
                if (form.fields.checkbox_group.fields[j].ngShow && form.fields.checkbox_group.fields[j].ngShow.indexOf(v) > -1) {
                    params.notification_configuration[form.fields.checkbox_group.fields[j].name] = Boolean($scope[form.fields.checkbox_group.fields[j].name]);
                }
            }

            Wait('start');
            Rest.setUrl(url);
            Rest.post(params)
                .success(function() {
                    $state.go('notifications', {}, { reload: true });
                    Wait('stop');
                })
                .error(function(data, status) {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to add new notifier. POST returned status: ' + status
                    });
                });
        };

        $scope.formCancel = function() {
            $state.go('notifications');
        };

    }
];
