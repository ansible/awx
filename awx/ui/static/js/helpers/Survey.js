/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
    /**
 * @ngdoc function
 * @name helpers.function:Schedules
 * @description
 *  Schedules Helper
 *
 *  Display the scheduler widget in a dialog
 *
 */

'use strict';

angular.module('SurveyHelper', [ 'Utilities', 'RestServices', 'SchedulesHelper', 'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'ModalDialog',
    'GeneratorHelpers'])

    .factory('ShowSurveyModal', ['Wait', 'CreateDialog', function(Wait, CreateDialog) {
        return function(params) {
            // Set modal dimensions based on viewport width

            var buttons,
                scope = params.scope,
                callback = params.callback,
                title = params.title;

            buttons = [{
                "label": "Cancel",
                "onClick": function() {
                    $(this).dialog('close');
                },
                "icon": "fa-times",
                "class": "btn btn-default",
                "id": "survey-close-button"
            },{
                "label": "Save",
                "onClick": function() {
                    setTimeout(function(){
                        scope.$apply(function(){
                            scope.saveSurvey();
                        });
                    });
                },
                "icon": "fa-check",
                "class": "btn btn-primary",
                "id": "survey-save-button"
            }];

            CreateDialog({
                id: 'survey-modal-dialog',
                title: title,
                scope: scope,
                buttons: buttons,
                width: 700,
                height: 725,
                minWidth: 400,
                onClose: function() {
                    $('#survey-modal-dialog #form-container').empty();
                },
                onOpen: function() {
                    Wait('stop');
                    $('#survey-tabs a:first').tab('show');
                    //  $('#surveyName').focus();
                    // $('#rrule_nlp_description').dblclick(function() {
                    //     setTimeout(function() { scope.$apply(function() { scope.showRRule = (scope.showRRule) ? false : true; }); }, 100);
                    // });
                },
                callback: callback
            });
        };
    }])

    .factory('EditSurvey', ['$routeParams','SchedulerInit', 'ShowSurveyModal', 'Wait', 'Rest', 'ProcessErrors', 'GetBasePath', 'GenerateForm', 'SurveyMakerForm',
            'Empty', 'AddSurvey',
    function($routeParams, SchedulerInit, ShowSurveyModal, Wait, Rest, ProcessErrors, GetBasePath, GenerateForm,SurveyMakerForm,
        Empty, AddSurvey) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                // callback = params.callback,
                tempSurv = {},
                generator = GenerateForm,
                form = SurveyMakerForm,
                labels={
                    "type": "Type",
                    "question_name": "Question Text",
                    "question_description": "Question Description",
                    "variable": "Answer Varaible Name",
                    "choices": "Choices",
                    "min": "Min",
                    "max": "Max",
                    "required": "Required",
                    "default": "Default Answer"
                },
                url = GetBasePath('job_templates') + id + '/survey_spec/', i;

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                    $('#survey-modal-dialog').dialog('open');
                // $('#schedulerName').focus();
                // setTimeout(function() {
                //     scope.$apply(function() {
                //         scheduler.setRRule(schedule.rrule);
                //         scheduler.setName(schedule.name);
                //     });
                // }, 300);
                });


            // scope.saveSurvey = function() {
            //     Wait('start');
            //     if(scope.mode==="add"){
            //         $('#survey-modal-dialog').dialog('close');
            //         scope.$emit('SurveySaved');
            //     }
            //     else{
            //         // var url = data.url+ 'survey_spec/';
            //         Rest.setUrl(url);
            //         Rest.post({ name: scope.survey_name, description: scope.survey_description, spec: scope.survey_questions })
            //             .success(function () {
            //                 // Wait('stop');
            //                 $('#survey-modal-dialog').dialog('close');
            //                 scope.$emit('SurveySaved');
            //             })
            //             .error(function (data, status) {
            //                 ProcessErrors(scope, data, status, form, { hdr: 'Error!',
            //                     msg: 'Failed to add new survey. Post returned status: ' + status });
            //             });
            //     }
            // };

            Wait('start');
            if(scope.mode === 'add'){
                tempSurv.survey_name = scope.survey_name;
                tempSurv.survey_description = scope.survey_description;
                generator.inject(form, { id: 'survey-modal-dialog' , mode: 'edit', related: false, scope: scope, breadCrumbs: false });

                ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });

                scope.survey_name = tempSurv.survey_name;
                scope.survey_description = tempSurv.survey_description;
                // scope.survey_questions = data.spec;
                for(i=0; i<scope.survey_questions.length; i++){
                    scope.finalizeQuestion(scope.survey_questions[i], labels);
                }
            }
            else{
                // Get the existing record
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                            if(!Empty(data)){
                                generator.inject(form, { id: 'survey-modal-dialog' , mode: 'edit', related: false, scope: scope, breadCrumbs: false });
                                ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });

                                scope.survey_name = data.name;
                                scope.survey_description = data.description;
                                scope.survey_questions = data.spec;
                                for(i=0; i<scope.survey_questions.length; i++){
                                    scope.finalizeQuestion(scope.survey_questions[i], labels);
                                }

                                Wait('stop');
                            } else {
                                AddSurvey({
                                    scope: scope
                                });
                            }

                        })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
                    });
            }
        };
    }])

    .factory('AddSurvey', ['$location', '$routeParams', 'SchedulerInit', 'ShowSurveyModal', 'Wait', 'GetBasePath', 'Empty',
        'SchedulePost', 'GenerateForm', 'SurveyMakerForm',
    function($location, $routeParams, SchedulerInit, ShowSurveyModal, Wait, GetBasePath, Empty, SchedulePost, GenerateForm, SurveyMakerForm) {
        return function(params) {
            var scope = params.scope,
                // callback= params.callback,
                // base = $location.path().replace(/^\//, '').split('/')[0],
                // url =  GetBasePath(base),
                generator = GenerateForm,
                form = SurveyMakerForm;

            // if (!Empty($routeParams.template_id)) {
            //     url += $routeParams.template_id + '/survey_spec/';
            // }
            // else if (!Empty($routeParams.id)) {
            //     url += $routeParams.id + '/survey_spec/';
            // }

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                scope.addQuestion();
                $('#survey-modal-dialog').dialog('open');
                // $('#surveyName').focus();
            });

            Wait('start');
            $('#form-container').empty();


            generator.inject(form, { id: 'survey-modal-dialog' , mode: 'add', related: false, scope: scope, breadCrumbs: false });
            ShowSurveyModal({ title: "Add Survey", scope: scope, callback: 'DialogReady' });

            if (scope.removeScheduleSaved) {
                scope.removeScheduleSaved();
            }
            scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
                Wait('stop');
                $('#survey-modal-dialog').dialog('close');
                scope.$emit('surveySaved');
            });

            // scope.saveSurvey = function() {
            //     Wait('start');
            //     $('#survey-modal-dialog').dialog('close');
            //     scope.$emit('SurveySaved');
            // };
        };
    }])

    .factory('SchedulePost', ['Rest', 'ProcessErrors', 'RRuleToAPI', 'Wait', function(Rest, ProcessErrors, RRuleToAPI, Wait) {
        return function(params) {
            var scope = params.scope,
                url = params.url,
                scheduler = params.scheduler,
                mode = params.mode,
                schedule = (params.schedule) ? params.schedule : {},
                callback = params.callback,
                newSchedule, rrule;

            if (scheduler.isValid()) {
                Wait('start');
                newSchedule = scheduler.getValue();
                rrule = scheduler.getRRule();
                schedule.name = newSchedule.name;
                schedule.rrule = RRuleToAPI(rrule.toString());
                schedule.description = (/error/.test(rrule.toText())) ? '' : rrule.toText();
                Rest.setUrl(url);
                if (mode === 'add') {
                    Rest.post(schedule)
                        .success(function(){
                            if (callback) {
                                scope.$emit(callback);
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error(function(data, status){
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });
                        });
                }
                else {
                    Rest.put(schedule)
                        .success(function(){
                            if (callback) {
                                scope.$emit(callback);
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error(function(data, status){
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });
                        });
                }
            }
            else {
                return false;
            }
        };
    }])

    /**
     * Inject the scheduler_dialog.html wherever needed
     */
    .factory('LoadDialogPartial', ['Rest', '$compile', 'ProcessErrors', function(Rest, $compile, ProcessErrors) {
        return function(params) {

            var scope = params.scope,
                element_id = params.element_id,
                callback = params.callback,
                url;

            // Add the schedule_dialog.html partial
            url = '/static/partials/schedule_dialog.html';
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    var e = angular.element(document.getElementById(element_id));
                    e.append(data);
                    $compile(e)(scope);
                    scope.$emit(callback);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. GET returned: ' + status });
                });
        };
    }])

    /**
     * Flip a schedule's enable flag
     *
     * ToggleSchedule({
     *     scope:       scope,
     *     id:          schedule.id to update
     *     callback:    scope.$emit label to call when update completes
     * });
     *
     */
    .factory('ToggleSchedule', ['Wait', 'GetBasePath', 'ProcessErrors', 'Rest', function(Wait, GetBasePath, ProcessErrors, Rest) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                callback = params.callback,
                url = GetBasePath('schedules') + id +'/';

            // Perform the update
            if (scope.removeScheduleFound) {
                scope.removeScheduleFound();
            }
            scope.removeScheduleFound = scope.$on('ScheduleFound', function(e, data) {
                data.enabled = (data.enabled) ? false : true;
                Rest.put(data)
                    .success( function() {
                        if (callback) {
                            scope.$emit(callback, id);
                        }
                        else {
                            Wait('stop');
                        }
                    })
                    .error( function() {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to update schedule ' + id + ' PUT returned: ' + status });
                    });
            });

            Wait('start');

            // Get the schedule
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    scope.$emit('ScheduleFound', data);
                })
                .error(function(data,status){
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve schedule ' + id + ' GET returned: ' + status });
                });
        };
    }])

    /**
     * Delete a survey. Prompts user to confirm delete
     *
     * DeleteSurvey({
     *     scope:       $scope containing list of survey form fields
     *     id:          id of job template that survey is attached to
     *     callback:    $scope.$emit label to call when delete is completed
     * })
     *
     */
    .factory('DeleteSurvey', ['GetBasePath','Rest', 'Wait', 'ProcessErrors',
    function(GetBasePath, Rest, Wait, ProcessErrors) {
        return function(params) {

            var scope = params.scope,
                id = params.id,
                // callback = params.callback,
                url;


            if (scope.removeSurveyDeleted) {
                scope.removeSurveyDeleted();
            }
            scope.$on('SurveyDeleted', function(){
                scope.survey_name = "";
                scope.survey_description = "";
                scope.survey_questions = [];
                Wait('stop');
                $('#job_templates_delete_survey_btn').hide();
                $('#job_templates_edit_survey_btn').hide();
                $('#job_templates_create_survey_btn').show();
            });


            Wait('start');

            if(scope.mode==="add"){
                scope.$emit("SurveyDeleted");

            } else {
                url = GetBasePath('job_templates')+ id + '/survey_spec/';

                Rest.setUrl(url);
                Rest.post({})
                    .success(function () {
                        scope.$emit("SurveyDeleted");

                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, { hdr: 'Error!',
                            msg: 'Failed to add new survey. Post returned status: ' + status });
                    });
            }
        };
    }])

    /**
     * Convert rrule string to an API agreeable format
     *
     */
    .factory('RRuleToAPI', [ function() {
        return function(rrule) {
            var response;
            response = rrule.replace(/(^.*(?=DTSTART))(DTSTART=.*?;)(.*$)/, function(str, p1, p2, p3) {
                return p2.replace(/\;/,'').replace(/=/,':') + ' ' + 'RRULE:' + p1 + p3;
            });
            return response;
        };
    }])


    .factory('SurveyControllerInit', ['$location', 'DeleteSurvey', 'EditSurvey', 'AddSurvey', 'GenerateForm', 'SurveyQuestionForm', 'Wait', 'Alert',
            'GetBasePath', 'Rest', 'ProcessErrors' ,
        function($location, DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert, GetBasePath, Rest, ProcessErrors) {
        return function(params) {
            var scope = params.scope,
                // parent_scope = params.parent_scope,
                id = params.id,
                url;
                // iterator = (params.iterator) ? params.iterator : scope.iterator,
                // base = $location.path().replace(/^\//, '').split('/')[0];

            scope.survey_questions = [];
            scope.answer_types=[
                {name: 'Text' , type: 'text'},
                {name: 'Textarea', type: 'textarea'},
                {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
                {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
                {name: 'JSON', type: 'json'},
                {name: 'Integer', type: 'integer'},
                {name: 'Float', type: 'number'}
            ];

            scope.deleteSurvey = function() {
                DeleteSurvey({
                    scope: scope,
                    id: id,
                    // callback: 'SchedulesRefresh'
                });
            };

            scope.editSurvey = function() {
                EditSurvey({
                    scope: scope,
                    id: id,
                    // callback: 'SchedulesRefresh'
                });
            };

            scope.addSurvey = function() {
                AddSurvey({
                    scope: scope,
                    // callback: 'SchedulesRefresh'
                });
            };
            scope.addQuestion = function(){
                GenerateForm.inject(SurveyQuestionForm, { id:'new_question', scope:scope, breadCrumbs: false});
            };

            scope.finalizeQuestion= function(data, labels){
                var key,
                html = '<div class="question_final row">';

                for (key in data) {
                    html+='<div class="col-xs-6"><label for="question_text"><span class="label-text">'+labels[key] +':  </span></label>'+data[key]+'</div>\n';
                }

                html+='</div>';

                $('#finalized_questions').before(html);
                $('#add_question_btn').show();
                $('#add_question_btn').removeAttr('disabled');
                $('#survey_maker_save_btn').removeAttr('disabled');
            };

            scope.addNewQuestion = function(){
            // $('#add_question_btn').on("click" , function(){
                scope.addQuestion();
                $('#add_question_btn').attr('disabled', 'disabled');
            // });
            };
            scope.submitQuestion = function(){
                var form = SurveyQuestionForm,
                data = {},
                labels={},
                min= "min",
                max = "max",
                fld;
                //generator.clearApiErrors();
                Wait('start');

                try {
                    for (fld in form.fields) {
                        if(scope[fld]){
                            if(fld === "type"){
                                data[fld] = scope[fld].type;
                                if(scope[fld].type==="integer" || scope[fld].type==="float"){
                                    data[min] = $('#answer_min').val();
                                    data[max] = $('#answer_max').val();
                                    labels[min]= "Min";
                                    labels[max]= "Max";
                                }
                            }
                            else{
                                data[fld] = scope[fld];
                            }
                            labels[fld] = form.fields[fld].label;
                        }
                    }
                    Wait('stop');
                    scope.survey_questions.push(data);
                    $('#new_question .aw-form-well').remove();
                    // for(fld in form.fields){
                    //     $scope[fld] = '';
                    // }
                    scope.finalizeQuestion(data , labels);

                } catch (err) {
                    Wait('stop');
                    Alert("Error", "Error parsing extra variables. Parser returned: " + err);
                }
            };

            scope.saveSurvey = function() {
                Wait('start');
                if(scope.mode==="add"){
                    $('#survey-modal-dialog').dialog('close');
                    scope.$emit('SurveySaved');
                }
                else{
                    url = GetBasePath('job_templates') + id + '/survey_spec/';
                    Rest.setUrl(url);
                    Rest.post({ name: scope.survey_name, description: scope.survey_description, spec: scope.survey_questions })
                        .success(function () {
                            // Wait('stop');
                            $('#survey-modal-dialog').dialog('close');
                            scope.$emit('SurveySaved');
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, { hdr: 'Error!',
                                msg: 'Failed to add new survey. Post returned status: ' + status });
                        });
                }
            };
        };
    }])

    .factory('SchedulesListInit', [ function() {
        return function(params) {
            var scope = params.scope,
                list = params.list,
                choices = params.choices;
            scope[list.name].forEach(function(item, item_idx) {
                var fld, field,
                    itm = scope[list.name][item_idx];
                itm.enabled = (itm.enabled) ? true : false;
                if (itm.enabled) {
                    itm.play_tip = 'Schedule is active. Click to stop.';
                    itm.status = 'active';
                    itm.status_tip = 'Schedule is active. Click to stop.';
                }
                else {
                    itm.play_tip = 'Schedule is stopped. Click to activate.';
                    itm.status = 'stopped';
                    itm.status_tip = 'Schedule is stopped. Click to activate.';
                }
                itm.nameTip = item.name + " schedule. Click to edit.";
                // Copy summary_field values
                for (field in list.fields) {
                    fld = list.fields[field];
                    if (fld.sourceModel) {
                        if (itm.summary_fields[fld.sourceModel]) {
                            itm[field] = itm.summary_fields[fld.sourceModel][fld.sourceField];
                        }
                    }
                }
                // Set the item type label
                if (list.fields.type) {
                    choices.every(function(choice) {
                        if (choice.value === item.type) {
                            itm.type_label = choice.label;
                            return false;
                        }
                        return true;
                    });
                }
            });
        };
    }])

    /**
     *
     *  Called from a controller to setup the scope for a schedules list
     *
     */
    .factory('LoadSchedulesScope', ['$compile', '$location', '$routeParams','SearchInit', 'PaginateInit', 'GenerateList', 'SchedulesControllerInit',
        'SchedulesListInit', 'SearchWidget',
        function($compile, $location, $routeParams, SearchInit, PaginateInit, GenerateList, SchedulesControllerInit, SchedulesListInit, SearchWidget) {
        return function(params) {
            var parent_scope = params.parent_scope,
                scope = params.scope,
                list = params.list,
                id = params.id,
                url = params.url,
                pageSize = params.pageSize || 5,
                spinner = (params.spinner === undefined) ? true : params.spinner,
                base = $location.path().replace(/^\//, '').split('/')[0],
                e, html;

            if (base === 'jobs') {
                // on jobs page the search widget appears on the right
                html = SearchWidget({
                    iterator: list.iterator,
                    template: params.list,
                    includeSize: false
                });
                e = angular.element(document.getElementById(id + '-search-container')).append(html);
                $compile(e)(scope);
                GenerateList.inject(list, {
                    mode: 'edit',
                    id: id,
                    breadCrumbs: false,
                    scope: scope,
                    showSearch: false
                });
            }
            else {
                GenerateList.inject(list, {
                    mode: 'edit',
                    id: id,
                    breadCrumbs: false,
                    scope: scope,
                    searchSize: 'col-lg-6 col-md-6 col-sm-6 col-xs-12',
                    showSearch: true
                });
            }

            SearchInit({
                scope: scope,
                set: list.name,
                list: list,
                url: url
            });

            PaginateInit({
                scope: scope,
                list: list,
                url: url,
                pageSize: pageSize
            });

            scope.iterator = list.iterator;

            if (scope.removePostRefresh) {
                scope.removePostRefresh();
            }
            scope.$on('PostRefresh', function(){
                SchedulesControllerInit({
                    scope: scope,
                    parent_scope: parent_scope,
                    list: list
                });
                SchedulesListInit({
                    scope: scope,
                    list: list,
                    choices: parent_scope.type_choices
                });
                parent_scope.$emit('listLoaded');
            });

            if ($routeParams.id__int) {
                scope[list.iterator + 'SearchField'] = 'id';
                scope[list.iterator + 'SearchValue'] = $routeParams.id__int;
                scope[list.iterator + 'SearchFieldLabel'] = 'ID';
            }

            scope.search(list.iterator, null, null, null, null, spinner);
        };
    }]);
