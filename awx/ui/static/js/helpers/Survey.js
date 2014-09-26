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
                // labels={
                //     "type": "Type",
                //     "question_name": "Question Text",
                //     "question_description": "Question Description",
                //     "variable": "Answer Varaible Name",
                //     "choices": "Choices",
                //     "min": "Min",
                //     "max": "Max",
                //     "required": "Required",
                //     "default": "Default Answer"
                // },
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
                    scope.finalizeQuestion(scope.survey_questions[i], i);
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
                                    scope.finalizeQuestion(scope.survey_questions[i], i);
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
                index = params.index,
                // url,
                // key,
                element, choices, i, checked,
                max, min, defaultValue,

            html = "";

            question.index = index;

            if(!$('#question_'+question.index+':eq(0)').is('div')){
                html+='<div id="question_'+question.index+'" class="question_final row"></div>';
                $('#finalized_questions').append(html);
            }



            html = '<div class="col-xs-12"><b>'+question.question_name+'</b></div>\n';
            if(!Empty(question.question_description)){
                html += '<div class="col-xs-12"><i>'+question.question_description+'</i></div>\n';
            }
            defaultValue = (question.default) ? question.default : "";

            if(question.type === 'text' ){
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="text" placeholder="'+defaultValue+'"  class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" >'+
                    '</div></div>';
            }
            if(question.type === "textarea"){
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<textarea class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" rows="3">'+defaultValue+'</textarea>'+
                    '</div></div>';
            }
            if(question.type === 'multiplechoice' || question.type === "multiselect"){
                choices = question.choices.split(/\n/);
                element = (question.type==="multiselect") ? "checkbox" : 'radio';

                for( i = 0; i<choices.length; i++){
                    checked = (!Empty(question.default) && question.default.indexOf(choices[i])!==-1) ? "checked" : "";
                    html+='<label class="'+element+'-inline final">'+
                    '<input type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[i]+' " '+checked+'>' +choices[i]+
                    '</label>';
                }

            }
            if(question.type === 'integer' || question.type === "float"){
                min = (question.min) ? question.min : "";
                max = (question.max) ? question.max : "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="number" class="final" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'">'+
                    '</div></div>';

            }
            html += '<div class="col-xs-12 text-right" id="question_actions">';
            html += '<a id="edit-question_'+question.index+'" data-placement="top" aw-tool-tip="Edit question" data-original-title="" title=""><i class="fa fa-pencil"></i> </a>';
            html += '<a id="delete-question_'+question.index+'" data-placement="top" aw-tool-tip="Delete question" data-original-title="" title=""><i class="fa fa-trash-o"></i> </a>';
            html += '<a id="question-up_'+question.index+'" data-placement="top" aw-tool-tip="Move up" data-original-title="" title=""><i class="fa fa-arrow-up"></i> </a>';
            html += '<a id="question-down_'+question.index+'" data-placement="top" aw-tool-tip="Move down" data-original-title="" title=""><i class="fa fa-arrow-down"></i> </a>';
            html+='</div></div>';

            $('#question_'+question.index).append(html);

            element = angular.element(document.getElementById('question_'+question.index));
            // element.html(html);
            $compile(element)(scope);
            // var questionScope = scope.$new;

            $('#add_question_btn').show();
            $('#add_question_btn').removeAttr('disabled');
            $('#survey_maker_save_btn').removeAttr('disabled');

            $('#delete-question_'+question.index+'').on('click', function($event){
                scope.deleteQuestion($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
            });
            $('#edit-question_'+question.index+'').on('click', function($event){
                scope.editQuestion($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
            });
            $('#question-up_'+question.index+'').on('click', function($event){
                scope.questionUp($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
            });
            $('#question-down_'+question.index+'').on('click', function($event){
                scope.questionDown($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
            });
        };
    }])


     .factory('EditQuestion', ['GetBasePath','Rest', 'Wait', 'ProcessErrors', '$compile', 'GenerateForm', 'SurveyQuestionForm',
    function(GetBasePath, Rest, Wait, ProcessErrors, $compile, GenerateForm, SurveyQuestionForm) {
        return function(params) {

            var scope = params.scope,
                index = params.index,
                element, fld, i,
                form = SurveyQuestionForm;
            $('#add_question_btn').hide();
            $('#new_question .aw-form-well').remove();
            element = $('.question_final:eq('+index+')');
            // element.attr('id', 'question_'+index);
            element.empty();
            // $('#new_question .aw-form-well').remove();
            GenerateForm.inject(form, { id: 'question_'+index, mode: 'edit' , scope:scope, breadCrumbs: false});
            for(fld in form.fields){
                if(form.fields[fld].type === 'select'){
                    for (i = 0; i < scope.answer_types.length; i++) {
                        if (scope.survey_questions[index][fld] === scope.answer_types[i].type) {
                            scope[fld] = scope.answer_types[i];
                        }
                    }
                } else {
                    scope[fld] = scope.survey_questions[index][fld];
                }
            }
        };
    }])

     .factory('DeleteQuestion' ,
    function() {
        return function(params) {

            var scope = params.scope,
                index = params.index,
                element;

            element = $('.question_final:eq('+index+')');
            // element.attr('id', 'question_'+index);
            element.remove();
            scope.survey_questions.splice(index, 1);
            scope.reorder();
        };
    })

    .factory('SurveyControllerInit', ['$location', 'DeleteSurvey', 'EditSurvey', 'AddSurvey', 'GenerateForm', 'SurveyQuestionForm', 'Wait', 'Alert',
            'GetBasePath', 'Rest', 'ProcessErrors' , '$compile', 'FinalizeQuestion', 'EditQuestion', 'DeleteQuestion',
        function($location, DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert,
            GetBasePath, Rest, ProcessErrors, $compile, FinalizeQuestion, EditQuestion, DeleteQuestion) {
        return function(params) {
            var scope = params.scope,
                // parent_scope = params.parent_scope,
                id = params.id,
                i, url;
                // iterator = (params.iterator) ? params.iterator : scope.iterator,
                // base = $location.path().replace(/^\//, '').split('/')[0];

            scope.survey_questions = [];
            scope.answer_types=[
                {name: 'Text' , type: 'text'},
                {name: 'Textarea', type: 'textarea'},
                {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
                {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
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

            scope.editQuestion = function(index){
                EditQuestion({
                    index: index,
                    scope: scope
                });
            };

            scope.deleteQuestion = function(index){
                DeleteQuestion({
                    index:index,
                    scope: scope
                });
            };

            scope.questionUp = function(index){
                var animating = false,
                    clickedDiv = $('#question_'+index),
                    prevDiv = clickedDiv.prev(),
                    distance = clickedDiv.outerHeight();

                if (animating) {
                    return;
                }

                if (prevDiv.length) {
                    animating = true;
                    $.when(clickedDiv.animate({
                        top: -distance
                    }, 600),
                    prevDiv.animate({
                        top: distance
                    }, 600)).done(function () {
                        prevDiv.css('top', '0px');
                        clickedDiv.css('top', '0px');
                        clickedDiv.insertBefore(prevDiv);
                        animating = false;
                        i = scope.survey_questions[index];
                        scope.survey_questions[index] = scope.survey_questions[index-1];
                        scope.survey_questions[index-1] = i;
                        scope.reorder();
                    });
                }
            };

            scope.questionDown = function(index){
                var clickedDiv = $('#question_'+index),
                    nextDiv = clickedDiv.next(),
                    distance = clickedDiv.outerHeight(),
                    animating = false;

                if (animating) {
                    return;
                }

                if (nextDiv.length) {
                    animating = true;
                    $.when(clickedDiv.animate({
                        top: distance
                    }, 600),
                    nextDiv.animate({
                        top: -distance
                    }, 600)).done(function () {
                        nextDiv.css('top', '0px');
                        clickedDiv.css('top', '0px');
                        nextDiv.insertBefore(clickedDiv);
                        animating = false;
                        i = scope.survey_questions[index];
                        scope.survey_questions[index] = scope.survey_questions[Number(index)+1];
                        scope.survey_questions[Number(index)+1] = i;
                        scope.reorder();
                    });
                }
            };

            scope.reorder = function(){
                for(i=0; i<scope.survey_questions.length; i++){
                    scope.survey_questions[i].index=i;
                    $('.question_final:eq('+i+')').attr('id', 'question_'+i);
                    // $('#delete-question_'+question.index+'')
                }
            };

            scope.finalizeQuestion= function(data, index){
                FinalizeQuestion({
                    scope: scope,
                    question: data,
                    id: id,
                    index: index
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
                fld, key, elementID;
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

                    if(GenerateForm.mode === 'add'){
                        scope.survey_questions.push(data);
                        $('#new_question .aw-form-well').remove();
                        // scope.addQuestion()
                        $('#add_question_btn').show();
                        scope.finalizeQuestion(data , scope.survey_questions.length-1);
                    }
                    if(GenerateForm.mode === 'edit'){
                        elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.id;
                        key = elementID.split('_')[1];
                        scope.survey_questions[key] = data;
                        $('#'+elementID).empty();
                        scope.finalizeQuestion(data , key);
                    }



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


