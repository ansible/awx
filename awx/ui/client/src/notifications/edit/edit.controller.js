/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'Wait',
    'NotificationsFormObject', 'ProcessErrors', 'GetBasePath',
    'GenerateForm',
    'notification_template',
    '$scope', '$state', 'GetChoices', 'CreateSelect2', 'Empty',
    'NotificationsTypeChange', 'ParseTypeChange', 'i18n',
    'MessageUtils', '$filter',
    function(
        Rest, Wait,
        NotificationsFormObject, ProcessErrors, GetBasePath,
        GenerateForm,
        notification_template,
        $scope, $state, GetChoices, CreateSelect2, Empty,
        NotificationsTypeChange, ParseTypeChange, i18n,
        MessageUtils, $filter
    ) {
        var generator = GenerateForm,
            id = notification_template.id,
            form = NotificationsFormObject,
            main = {},
            url = GetBasePath('notification_templates'),
            defaultMessages = {};

        init();

        function init() {
            $scope.notification_template = notification_template;

            $scope.$watch('notification_template.summary_fields.user_capabilities.edit', function(val) {
                if (val === false) {
                    $scope.canAdd = false;
                }
            });

            Rest.setUrl(GetBasePath('notification_templates'));
            Rest.options()
                .then(({data}) => {
                    defaultMessages = data.actions.GET.messages;
                });

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

            Wait('start');
            Rest.setUrl(url + id + '/');
            Rest.get()
                .then(({data}) => {
                    var fld;
                    for (fld in form.fields) {
                        if (data[fld]) {
                            $scope[fld] = data[fld];
                            main[fld] = data[fld];
                        }

                        if(data.notification_configuration.use_ssl === true){
                            $scope.email_options = "use_ssl";
                            main.email_options = "use_ssl";
                            $scope.use_ssl = true;
                            main.use_ssl = true;
                            $scope.use_tls = false;
                            main.use_tls = false;
                        }

                        if(data.notification_configuration.use_tls === true){
                            $scope.email_options = "use_tls";
                            main.email_options = "use_tls";
                            $scope.use_ssl = false;
                            main.use_ssl = false;
                            $scope.use_tls = true;
                            main.use_tls = true;
                        }

                        if (data.notification_configuration.timeout === null ||
                            !data.notification_configuration.timeout){
                            $scope.timeout = 30;
                        }

                        if (data.notification_configuration[fld]) {
                            $scope[fld] = data.notification_configuration[fld];
                            main[fld] = data.notification_configuration[fld];

                            if (form.fields[fld].type === 'textarea') {
                                if (form.fields[fld].name === 'headers') {
                                    $scope[fld] = JSON.stringify($scope[fld], null, 2);
                                } else {
                                    $scope[fld] = $scope[fld].join('\n');
                                }
                            }
                        }

                        if (form.fields[fld].sourceModel && data.summary_fields &&
                            data.summary_fields[form.fields[fld].sourceModel]) {
                            $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                            main[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        }
                    }
                    data.notification_type = (Empty(data.notification_type)) ? '' : data.notification_type;
                    for (var i = 0; i < $scope.notification_type_options.length; i++) {
                        if ($scope.notification_type_options[i].value === data.notification_type) {
                            $scope.notification_type = $scope.notification_type_options[i];
                            break;
                        }
                    }

                    main.notification_type = $scope.notification_type;
                    CreateSelect2({
                        element: '#notification_template_notification_type',
                        multiple: false
                    });
                    
                    $scope.emailOptions = [
                        {'id': 'use_tls', 'name': i18n._('Use TLS')},
                        {'id': 'use_ssl', 'name': i18n._('Use SSL')},
                    ];
                    CreateSelect2({
                        element: '#notification_template_email_options',
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

                    $scope.httpMethodChoices = [
                        {'id': 'POST', 'name': i18n._('POST')},
                        {'id': 'PUT', 'name': i18n._('PUT')},
                    ];
                    CreateSelect2({
                        element: '#notification_template_http_method',
                        multiple: false,
                    });

                    NotificationsTypeChange.getDetailFields($scope.notification_type.value).forEach(function(field) {
                        $scope[field[0]] = field[1];
                    });
                    $scope.notification_obj = data;

                    $scope.parse_type = 'json';
                    if (!$scope.headers) {
                        $scope.headers = "{\n}";
                    }

                    ParseTypeChange({
                        scope: $scope,
                        parse_variable: 'parse_type',
                        variable: 'headers',
                        field_id: 'notification_template_headers',
                        readOnly: !$scope.notification_template.summary_fields.user_capabilities.edit
                    });

                    MessageUtils.setMessagesOnScope($scope, data.messages, defaultMessages);

                    Wait('stop');
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: 'Failed to retrieve notification: ' + id + '. GET status: ' + status
                    });
                });
        });

        $scope.$watch('headers', function validate_headers(str) {
            try {
                const headers = typeof str === 'string' ? JSON.parse(str) : str;
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
                    }
                    if ($scope.timeout === null || !$scope.timeout) {
                        $scope.timeout = 30;
                    }
                    else {
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
                field_id: 'notification_template_headers',
                readOnly: !$scope.notification_template.summary_fields.user_capabilities.edit
            });
        };

        $scope.$watch('customize_messages', (value) => {
            if (value) {
                $scope.$broadcast('reset-code-mirror', {
                    customize_messages: $scope.customize_messages,
                });
            }
        });
        $scope.toggleForm = function(key) {
            $scope[key] = !$scope[key];
        };
        $scope.$watch('notification_type', (newValue, oldValue = {}) => {
            if (newValue) {
                MessageUtils.updateDefaultsOnScope(
                  $scope,
                  defaultMessages[oldValue.value],
                  defaultMessages[newValue.value]
                );
                $scope.$broadcast('reset-code-mirror', {
                    customize_messages: $scope.customize_messages,
                });
            }
        });

        $scope.formSave = function() {
            var params,
                v = $scope.notification_type.value;

            generator.clearApiErrors($scope);
            params = {
                "name": $scope.name,
                "description": $scope.description,
                "organization": $scope.organization,
                "messages": MessageUtils.getMessagesObj($scope, defaultMessages),
                "notification_type": v,
                "notification_configuration": {}
            };

            function processValue(value, i, field) {
                if (field.type === 'textarea') {
                    if (field.name === 'headers') {
                        if (typeof $scope[i] === 'string') {
                            $scope[i] = JSON.parse($scope[i]);
                        }
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
                const isUsernameIncluded = (
                  $scope.notification_type.value === 'email' ||
                  $scope.notification_type.value === 'webhook'
                );
                if (i === "username" && isUsernameIncluded &&
                  (value === null || value === undefined)) {
                    $scope[i] = "";
                }
                if (field.type === 'sensitive' && (value === null || value === undefined)) {
                    $scope[i] = "";
                }
                return $scope[i];
            }

            params.notification_configuration = _.fromPairs(Object.keys(form.fields)
                .filter(i => (form.fields[i].ngShow && form.fields[i].ngShow.indexOf(v) > -1))
                .map(i => [i, processValue($scope[i], i, form.fields[i])]));

            delete params.notification_configuration.email_options;

            params.notification_configuration.use_ssl = $scope.email_options === 'use_ssl';
            params.notification_configuration.use_tls = $scope.email_options === 'use_tls';            

            Wait('start');
            Rest.setUrl(url + id + '/');
            Rest.put(params)
                .then(() => {
                    $state.go('notifications', {}, { reload: true });
                    Wait('stop');
                })
                .catch(({ data, status }) => {
                    let description = 'PUT returned status: ' + status;
                    if (data && data.messages && data.messages.length > 0) {
                        description = _.uniq(data.messages).join(', ');
                    }
                    ProcessErrors($scope, data, status, form, {
                        hdr: 'Error!',
                        msg: $filter('sanitize')('Failed to update notifier. ' + description + '.')
                    });
                });
        };


        $scope.formCancel = function() {
            $state.go('notifications');
        };

    }
];
