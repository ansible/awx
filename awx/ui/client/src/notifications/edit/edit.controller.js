/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'Rest', 'Wait',
        'NotificationsFormObject', 'ProcessErrors', 'GetBasePath',
        'GenerateForm', 'SearchInit' , 'PaginateInit',
        'LookUpInit', 'OrganizationList', 'notifier',
        '$scope', '$state', 'GetChoices', 'CreateSelect2', 'Empty',
        '$rootScope', 'NotificationsTypeChange',
        function(
            Rest, Wait,
            NotificationsFormObject, ProcessErrors, GetBasePath,
            GenerateForm, SearchInit, PaginateInit,
            LookUpInit, OrganizationList, notifier,
            $scope, $state, GetChoices, CreateSelect2, Empty,
            $rootScope, NotificationsTypeChange
        ) {
            var generator = GenerateForm,
                id = notifier.id,
                form = NotificationsFormObject,
                master = {},
                url = GetBasePath('notifiers');

            $scope.notifier = notifier;
            generator.inject(form, {
                    mode: 'edit' ,
                    scope:$scope,
                    related: false
                });
                if ($scope.removeChoicesReady) {
                    $scope.removeChoicesReady();
                }
                $scope.removeChoicesReady = $scope.$on('choicesReady', function () {
                    var i;
                    for (i = 0; i < $scope.notification_type_options.length; i++) {
                        if ($scope.notification_type_options[i].value === '') {
                            $scope.notification_type_options[i].value="manual";
                            // $scope.scm_type = $scope.scm_type_options[i];
                            break;
                        }
                    }

                    Wait('start');
                    Rest.setUrl(url + id+'/');
                    Rest.get()
                        .success(function (data) {
                            var fld;
                            for (fld in form.fields) {
                                if (data[fld]) {
                                    $scope[fld] = data[fld];
                                    master[fld] = data[fld];
                                }

                                if(data.notification_configuration[fld]){
                                    $scope[fld] = data.notification_configuration[fld];
                                    master[fld] = data.notification_configuration[fld];

                                    if(form.fields[fld].type === 'textarea'){
                                        $scope[fld] = $scope[fld].toString().replace(',' , '\n');
                                    }
                                }

                                if (form.fields[fld].sourceModel && data.summary_fields &&
                                    data.summary_fields[form.fields[fld].sourceModel]) {
                                    $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                                    master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
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

                            // if ($scope.notification_type.value !== 'manual') {
                            //     $scope.pathRequired = false;
                            //     $scope.scmRequired = true;
                            // } else {
                            //     $scope.pathRequired = true;
                            //     $scope.scmRequired = false;
                            // }

                            master.notification_type = $scope.notification_type;
                            CreateSelect2({
                                element: '#notifier_notification_type',
                                multiple: false
                            });
                            NotificationsTypeChange.getDetailFields($scope.notification_type.value).forEach(function(field) {
                                $scope[field[0]] = field[1];
                            });
                            Wait('stop');
                        })
                        .error(function (data, status) {
                            ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                msg: 'Failed to retrieve notification: ' + id + '. GET status: ' + status });
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

            $scope.typeChange = function () {
                for(var fld in form.fields){
                    if(form.fields[fld] && form.fields[fld].subForm){
                        $scope[fld] = null;
                        $scope.notifier_form[fld].$setPristine();
                    }
                }

                NotificationsTypeChange.getDetailFields($scope.notification_type.value).forEach(function(field) {
                    $scope[field[0]] = field[1];
                });
            };

            $scope.formSave = function(){
                var params,
                    // config,
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
                        $scope[i] = $scope[i].toString().split('\n');
                    }
                    if(field.type === 'checkbox'){
                        $scope[i] = Boolean($scope[i]);
                    }
                    return $scope[i];

                }

                params.notification_configuration = _.object(Object.keys(form.fields)
                    .filter(i => (form.fields[i].ngShow &&  form.fields[i].ngShow.indexOf(v) > -1))
                    .map(i => [i, processValue($scope[i], i , form.fields[i])]));

                Wait('start');
                Rest.setUrl(url+ id+'/');
                Rest.put(params)
                .success(function (data) {
                    $rootScope.addedItem = data.id;
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
