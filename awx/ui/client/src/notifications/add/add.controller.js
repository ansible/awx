/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait', 'NotificationsFormObject',
    'ProcessErrors', 'GetBasePath', 'Alert',
    'GenerateForm', '$scope', '$state', 'CreateSelect2', 'GetChoices',
    'NotificationsTypeChange', 'ParseTypeChange', 'i18n',
    function(
        Rest, Wait, NotificationsFormObject,
        ProcessErrors, GetBasePath, Alert,
        GenerateForm, $scope, $state, CreateSelect2, GetChoices,
        NotificationsTypeChange, ParseTypeChange, i18n
    ) {

        var generator = GenerateForm,
            form = NotificationsFormObject,
            url = GetBasePath('notification_templates');

        init();

        function init() {
            Rest.setUrl(GetBasePath('notification_templates'));
            Rest.options()
                .then(({data}) => {
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

        if ($state.params && $state.params.organization_id) {
            let id = $state.params.organization_id,
                url = GetBasePath('organizations') + id + '/';

            Rest.setUrl(url);
            Rest.get()
                .then(({data}) => {
                    $scope.organization_name = data.name;
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: `Failed to retrieve organization. GET status: ${status}`
                    });
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

            $scope.hipchatColors = [
                {'id': 'gray', 'name': i18n._('Gray')},
                {'id': 'green', 'name': i18n._('Green')},
                {'id': 'purple', 'name': i18n._('Purple')},
                {'id': 'red', 'name': i18n._('Red')},
                {'id': 'yellow', 'name': i18n._('Yellow')},
                {'id': 'random', 'name': i18n._('Random')}
            ];
            CreateSelect2({
                element: '#notification_template_color',
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

        $scope.emailOptionsChange = function () {
            if ($scope.email_options === 'use_ssl') {
                if ($scope.use_ssl) {
                    $scope.email_options = null;
                    $scope.use_ssl = false;
                    return;
                }

                $scope.use_ssl = true;
                $scope.use_tls = false;
            }
            else if ($scope.email_options === 'use_tls') {
                if ($scope.use_tls) {
                    $scope.email_options = null;
                    $scope.use_tls = false;
                    return;
                }

                $scope.use_ssl = false;
                $scope.use_tls = true;
            }
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
                    }
                    else if (field.name === 'annotation_tags' && $scope.notification_type.value === "grafana" && value === null) {
                        $scope[i] = null;
                    }
                    else {
                        $scope[i] = $scope[i].toString().split('\n');
                    }
                }
                if (field.type === 'checkbox') {
                    $scope[i] = Boolean($scope[i]);
                }
                if (field.type === 'number') {
                    $scope[i] = Number($scope[i]);
                }
                if (i === "username" && $scope.notification_type.value === "email" && (value === null || !value
                )) {
                    $scope[i] = "";
                }
                if (field.type === 'sensitive' && (value === null || !value
                )) {
                    $scope[i] = "";
                }
                return $scope[i];
            }

            params.notification_configuration = _.fromPairs(Object.keys(form.fields)
                .filter(i => (form.fields[i].ngShow && form.fields[i].ngShow.indexOf(v) > -1))
                .map(i => [i, processValue($scope[i], i, form.fields[i])]));

                delete params.notification_configuration.email_options;

                for(var j = 0; j < form.fields.email_options.options.length; j++) {
                    if(form.fields.email_options.options[j].ngShow && form.fields.email_options.options[j].ngShow.indexOf(v) > -1) {
                        params.notification_configuration[form.fields.email_options.options[j].value] = Boolean($scope[form.fields.email_options.options[j].value]);
                    }
                }

            Wait('start');
            Rest.setUrl(url);
            Rest.post(params)
                .then(() => {
                    $state.go('notifications', {}, { reload: true });
                    Wait('stop');
                })
                .catch(({data, status}) => {
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
