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
            });


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
                                // scope.addQuestion();
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

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                scope.addQuestion();
                $('#survey-modal-dialog').dialog('open');
                // $('#surveyName').focus();
                // $('#question_unique_required_chbox').prop('checked' , true);
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
     * Takes a finalized question and displays it on the survey maker page
     *
     * FinalizeQuestion({
     *     scope:       $scope containing list of survey form fields
     *     question: question object that was submitted by the question form
     *     id:          id of job template that survey is attached to
     *     callback:    $scope.$emit label to call when delete is completed
     * })
     *
     */
    .factory('FinalizeQuestion', ['GetBasePath','Rest', 'Wait', 'ProcessErrors', '$compile', 'Empty',
    function(GetBasePath, Rest, Wait, ProcessErrors, $compile, Empty) {
        return function(params) {

            var scope = params.scope,
                // id = params.id,
                question = params.question,
                // callback = params.callback,
                // url,
                // key,
                element, choices, i, checked,
                max, min, defaultValue,

            html = '<div class="question_final row">';
            html += '<div class="col-xs-12"><b>'+question.question_name+'</b></div>\n';
            if(!Empty(question.question_description)){
                html += '<div class="col-xs-12">    '+question.question_description+'</div>\n';
            }
            defaultValue = (question.default) ? question.default : "";

            if(question.type === 'text' ){

                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="text" placeholder="'+defaultValue+'"  class="form-control ng-pristine ng-invalid-required ng-invalid" required="" >'+
                    '</div></div>';
            }
            if(question.type === "textarea"){
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<textarea class="form-control ng-pristine ng-invalid-required ng-invalid" required="" rows="3">'+defaultValue+'</textarea>'+
                    '</div></div>';
            }
            if(question.type === 'multiplechoice' || question.type === "multiselect"){
                choices = question.choices.split(/\n/);
                element = (question.type==="multiselect") ? "checkbox" : 'radio';

                for( i = 0; i<choices.length; i++){
                    checked = (!Empty(question.default) && question.default.indexOf(choices[i])!==-1) ? "checked" : "";
                    html+='<label class="'+element+'-inline">'+
                    '<input type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[i]+' " '+checked+'>' +choices[i]+
                    '</label>';
                }

            }
            if(question.type === 'integer' || question.type === "float"){
                min = (question.min) ? question.min : "";
                max = (question.max) ? question.max : "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="number" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'">'+
                    '</div></div>';

            }
            if(question.type === "json"){

            }
            html += '<div class="col-xs-12 text-right" id="question_actions">';
            html += '<a id="edit-action" data-placement="top" ng-click="editQuestion(this)" aw-tool-tip="Edit question" data-original-title="" title=""><i class="fa fa-pencil"></i> </a>';
            html += '<a id="delete-action" data-placement="top" ng-click="deleteQuestion(job_template.id, job_template.name)" aw-tool-tip="Delete template" data-original-title="" title=""><i class="fa fa-trash-o"></i> </a>';
            html += '<a id="edit-action" data-placement="top" ng-click="moveQuestion(this)" aw-tool-tip="Move up" data-original-title="" title=""><i class="fa fa-sort-desc"></i> </a>';
            html += '<a id="edit-action" data-placement="top" ng-click="editQuestion(this)" aw-tool-tip="Edit question" data-original-title="" title=""><i class="fa fa-sort-asc"></i> </a>';
            html+='</div></div>';

            $('#finalized_questions').append(html);

            element = angular.element(document.getElementById('finalized_questions'));
            // element.html(html);
            $compile(element)(scope);
            // var questionScope = scope.$new;

            $('#add_question_btn').show();
            $('#add_question_btn').removeAttr('disabled');
            $('#survey_maker_save_btn').removeAttr('disabled');
        };
    }])


    .factory('SurveyControllerInit', ['$location', 'DeleteSurvey', 'EditSurvey', 'AddSurvey', 'GenerateForm', 'SurveyQuestionForm', 'Wait', 'Alert',
            'GetBasePath', 'Rest', 'ProcessErrors' , '$compile', 'FinalizeQuestion',
        function($location, DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert,
            GetBasePath, Rest, ProcessErrors, $compile, FinalizeQuestion) {
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
                {name: 'Float', type: 'float'}
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
                GenerateForm.inject(SurveyQuestionForm, { id:'new_question', mode: 'add' , scope:scope, breadCrumbs: false});
                scope.required = true; //set the required checkbox to true via the ngmodel attached to scope.required.
            };
            scope.editQuestion = function(question){
                alert('success : ' + question);
            };

            scope.finalizeQuestion= function(data){
                FinalizeQuestion({
                    scope: scope,
                    question: data,
                    id: id,
                    //callback?
                });
            };

            scope.addNewQuestion = function(){
            // $('#add_question_btn').on("click" , function(){
                scope.addQuestion();
                $('#add_question_btn').attr('disabled', 'disabled');
                $('#add_question_btn').hide();
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
                    // scope.addQuestion()
                    $('#add_question_btn').show();
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
    }]);


