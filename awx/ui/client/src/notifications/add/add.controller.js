/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$rootScope', 'pagination', '$compile','SchedulerInit', 'Rest', 'Wait',
        'NotificationsFormObject', 'ProcessErrors', 'GetBasePath', 'Empty',
        'GenerateForm', 'SearchInit' , 'PaginateInit', 'LookUpInit',
        'OrganizationList', '$scope', '$state', 'CreateSelect2', 'GetChoices',
        'NotificationsTypeChange', 'ParseTypeChange',
        function(
            $rootScope, pagination, $compile, SchedulerInit, Rest, Wait,
            NotificationsFormObject, ProcessErrors, GetBasePath, Empty,
            GenerateForm, SearchInit, PaginateInit, LookUpInit,
            OrganizationList, $scope, $state, CreateSelect2, GetChoices,
            NotificationsTypeChange, ParseTypeChange
        ) {
            var generator = GenerateForm,
                form = NotificationsFormObject,
                url = GetBasePath('notification_templates');

            generator.inject(form, {
                mode: 'add' ,
                scope: $scope,
                related: false
            });
            generator.reset();

            if ($scope.removeChoicesReady) {
                $scope.removeChoicesReady();
            }
            $scope.removeChoicesReady = $scope.$on('choicesReady', function () {
                var i;
                for (i = 0; i < $scope.notification_type_options.length; i++) {
                    if ($scope.notification_type_options[i].value === '') {
                        $scope.notification_type_options[i].value="manual";
                        break;
                    }
                }
                CreateSelect2({
                    element: '#notification_template_notification_type',
                    multiple: false
                });
            });


            LookUpInit({
                    url: GetBasePath('organization'),
                    scope: $scope,
                    form: form,
                    list: OrganizationList,
                    field: 'organization',
                    input_type: 'radio'
                });

            GetChoices({
                scope: $scope,
                url: url,
                field: 'notification_type',
                variable: 'notification_type_options',
                callback: 'choicesReady'
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
                } catch (err) {
                }

                $scope.notification_template_form.headers.$setValidity('json', false);
            });

            $scope.typeChange = function () {
                for(var fld in form.fields){
                    if(form.fields[fld] && form.fields[fld].subForm){
                        $scope[fld] = null;
                        $scope.notification_template_form[fld].$setPristine();
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
            $scope.formSave = function () {
                var params,
                    v = $scope.notification_type.value;

                generator.clearApiErrors();
                params = {
                    "name" : $scope.name,
                    "description": $scope.description,
                    "organization": $scope.organization,
                    "notification_type" : v,
                    "notification_configuration": {}
                };

                function processValue(value, i , field){
                    if(field.type === 'textarea'){
                        if (field.name === 'headers') {
                            $scope[i] = JSON.parse($scope[i]);
                        } else {
                            $scope[i] = $scope[i].toString().split('\n');
                        }
                    }
                    if(field.type === 'checkbox'){
                        $scope[i] = Boolean($scope[i]);
                    }
                    if(field.type === 'number'){
                        $scope[i] = Number($scope[i]);
                    }
                    return $scope[i];
                }

                params.notification_configuration = _.object(Object.keys(form.fields)
                    .filter(i => (form.fields[i].ngShow &&  form.fields[i].ngShow.indexOf(v) > -1))
                    .map(i => [i, processValue($scope[i], i , form.fields[i])]));

                Wait('start');
                Rest.setUrl(url);
                Rest.post(params)
                .success(function () {
                    $state.go('notifications', {}, {reload: true});
                    Wait('stop');
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new notifier. POST returned status: ' + status });
                });
            };

            $scope.formCancel = function () {
                $state.transitionTo('notifications');
            };

        }
    ];
