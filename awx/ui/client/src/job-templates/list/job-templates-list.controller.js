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
        'LookUpInit', 'PlaybookRun', 'Wait', 'CreateDialog' , '$compile',
        '$state',

        function(
            $scope, $rootScope, $location, $log,
            $stateParams, Rest, Alert, JobTemplateList, GenerateList, Prompt,
            SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors,
            GetBasePath, JobTemplateForm, CredentialList, LookUpInit, PlaybookRun,
            Wait, CreateDialog, $compile, $state
        ) {

            ClearScope();

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
                $state.transitionTo('jobTemplates.edit', {template_id: id});
            };

            $scope.deleteJobTemplate = function (id, name) {
                var action = function () {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    var url = defaultUrl + id + '/';
                    Rest.setUrl(url);
                    Rest.destroy()
                        .success(function () {
                            $scope.search(list.iterator);
                        })
                        .error(function (data) {
                            Wait('stop');
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                };

                Prompt({
                    hdr: 'Delete',
                    body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the job template below?</div><div class="Prompt-bodyTarget">' + name + '</div>',
                    action: action,
                    actionText: 'DELETE'
                });
            };

            $scope.copyJobTemplate = function(id, name){
                var  element,
                      buttons = [{
                        "label": "Cancel",
                        "onClick": function() {
                            $(this).dialog('close');
                        },
                        "icon": "fa-times",
                        "class": "btn btn-default",
                        "id": "copy-close-button"
                    },{
                        "label": "Copy",
                        "onClick": function() {
                            copyAction();
                            // setTimeout(function(){
                            //     scope.$apply(function(){
                            //         if(mode==='survey-taker'){
                            //             scope.$emit('SurveyTakerCompleted');
                            //         } else{
                            //             scope.saveSurvey();
                            //         }
                            //     });
                            // });
                        },
                        "icon":  "fa-copy",
                        "class": "btn btn-primary",
                        "id": "job-copy-button"
                    }],
                    copyAction = function () {
                        // retrieve the copy of the job template object from the api, then overwrite the name and throw away the id
                        Wait('start');
                        var url = defaultUrl + id + '/';
                        Rest.setUrl(url);
                        Rest.get()
                            .success(function (data) {
                                data.name = $scope.new_copy_name;
                                delete data.id;
                                $scope.$emit('GoToCopy', data);
                            })
                            .error(function (data) {
                                Wait('stop');
                                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                    msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                            });
                    };


                CreateDialog({
                    id: 'copy-job-modal',
                    title: "Copy",
                    scope: $scope,
                    buttons: buttons,
                    width: 500,
                    height: 300,
                    minWidth: 200,
                    callback: 'CopyDialogReady'
                });

                $('#job_name').text(name);
                $('#copy-job-modal').show();


                if ($scope.removeCopyDialogReady) {
                    $scope.removeCopyDialogReady();
                }
                $scope.removeCopyDialogReady = $scope.$on('CopyDialogReady', function() {
                    //clear any old remaining text
                    $scope.new_copy_name = "" ;
                    $scope.copy_form.$setPristine();
                    $('#copy-job-modal').dialog('open');
                    $('#job-copy-button').attr('ng-disabled', "!copy_form.$valid");
                    element = angular.element(document.getElementById('job-copy-button'));
                    $compile(element)($scope);

                });

                if ($scope.removeGoToCopy) {
                    $scope.removeGoToCopy();
                }
                $scope.removeGoToCopy = $scope.$on('GoToCopy', function(e, data) {
                    var url = defaultUrl,
                    old_survey_url = (data.related.survey_spec) ? data.related.survey_spec : "" ;
                    Rest.setUrl(url);
                    Rest.post(data)
                        .success(function (data) {
                            if(data.survey_enabled===true){
                                $scope.$emit("CopySurvey", data, old_survey_url);
                            }
                            else {
                                $('#copy-job-modal').dialog('close');
                                Wait('stop');
                                $location.path($location.path() + '/' + data.id);
                            }

                        })
                        .error(function (data) {
                            Wait('stop');
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                });

                if ($scope.removeCopySurvey) {
                    $scope.removeCopySurvey();
                }
                $scope.removeCopySurvey = $scope.$on('CopySurvey', function(e, new_data, old_url) {
                    // var url = data.related.survey_spec;
                    Rest.setUrl(old_url);
                    Rest.get()
                        .success(function (survey_data) {

                            Rest.setUrl(new_data.related.survey_spec);
                            Rest.post(survey_data)
                            .success(function () {
                                $('#copy-job-modal').dialog('close');
                                Wait('stop');
                                $location.path($location.path() + '/' + new_data.id);
                            })
                            .error(function (data) {
                                Wait('stop');
                                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                    msg: 'Call to ' + new_data.related.survey_spec + ' failed. DELETE returned status: ' + status });
                            });


                        })
                        .error(function (data) {
                            Wait('stop');
                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + old_url + ' failed. DELETE returned status: ' + status });
                        });

                });

            };

            $scope.submitJob = function (id) {
                PlaybookRun({ scope: $scope, id: id });
            };

            $scope.scheduleJob = function (id) {
                $state.go('jobTemplateSchedules', {id: id});
            };
        }
    ];
