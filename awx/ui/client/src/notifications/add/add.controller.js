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
        'NotificationsTypeChange',
        function(
            $rootScope, pagination, $compile, SchedulerInit, Rest, Wait,
            NotificationsFormObject, ProcessErrors, GetBasePath, Empty,
            GenerateForm, SearchInit, PaginateInit, LookUpInit,
            OrganizationList, $scope, $state, CreateSelect2, GetChoices,
            NotificationsTypeChange
        ) {
            var generator = GenerateForm,
                form = NotificationsFormObject,
                url = GetBasePath('notifiers');

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
                    element: '#notifier_notification_type',
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
                        $scope[i] = $scope[i].toString().split('\n');
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
