/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$scope', '$rootScope', '$location', '$log',
        '$stateParams', 'Rest', 'Alert', 'JobTemplateList', 'generateList',
        'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
        'ProcessErrors', 'GetBasePath', 'JobTemplateForm', 'CredentialList',
        'LookUpInit', 'InitiatePlaybookRun', 'Wait', '$compile',
        '$state', '$filter', 'rbacUiControlService',

        function(
            $scope, $rootScope, $location, $log,
            $stateParams, Rest, Alert, JobTemplateList, GenerateList, Prompt,
            SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors,
            GetBasePath, JobTemplateForm, CredentialList, LookUpInit, InitiatePlaybookRun,
            Wait, $compile, $state, $filter, rbacUiControlService
        ) {
            ClearScope();

            $scope.canAdd = false;

            rbacUiControlService.canAdd("job_templates")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });

            var list = JobTemplateList,
                defaultUrl = GetBasePath('job_templates'),
                view = GenerateList,
                base = $location.path().replace(/^\//, '').split('/')[0],
                mode = (base === 'job_templates') ? 'edit' : 'select';

            view.inject(list, { mode: mode, scope: $scope });
            $rootScope.flashMessage = null;

            if ($scope.removePostRefresh) {
                $scope.removePostRefresh();
            }
            $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
                // Cleanup after a delete
                Wait('stop');
                $('#prompt-modal').modal('hide');
            });

            SearchInit({
                scope: $scope,
                set: 'job_templates',
                list: list,
                url: defaultUrl
            });
            PaginateInit({
                scope: $scope,
                list: list,
                url: defaultUrl
            });

            // Called from Inventories tab, host failed events link:
            if ($stateParams.name) {
                $scope[list.iterator + 'SearchField'] = 'name';
                $scope[list.iterator + 'SearchValue'] = $stateParams.name;
                $scope[list.iterator + 'SearchFieldLabel'] = list.fields.name.label;
            }

            $scope.search(list.iterator);

            $scope.addJobTemplate = function () {
                $state.transitionTo('jobTemplates.add');
            };

            $scope.editJobTemplate = function (id) {
                $state.transitionTo('jobTemplates.edit', {id: id});
            };

            $scope.deleteJobTemplate = function (id, name) {
                var action = function () {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    var url = defaultUrl + id + '/';
                    Rest.setUrl(url);
                    Rest.destroy()
                        .success(function () {
                            if (parseInt($state.params.id) === id) {
                                $state.go("^", null, {reload: true});
                            } else {
                                $scope.search(list.iterator);
                            }
                        })
                        .error(function (data) {
                            Wait('stop');
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                };

                Prompt({
                    hdr: 'Delete',
                    body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the job template below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
                    action: action,
                    actionText: 'DELETE'
                });
            };

            $scope.submitJob = function (id) {
                InitiatePlaybookRun({ scope: $scope, id: id });
            };

            $scope.scheduleJob = function (id) {
                $state.go('jobTemplateSchedules', {id: id});
            };
        }
    ];
