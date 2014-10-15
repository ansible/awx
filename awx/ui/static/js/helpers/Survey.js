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

    .factory('ShowSurveyModal', ['Wait', 'CreateDialog', 'Empty', '$compile' ,
        function(Wait, CreateDialog, Empty, $compile) {
        return function(params) {
            // Set modal dimensions based on viewport width

            var scope = params.scope,
                callback = params.callback,
                mode = (params.mode) ? params.mode : "survey-maker",
                title = params.title,
                element,
                target = (mode==='survey-taker') ? 'password-modal' : "survey-modal-dialog",
                buttons = [{
                "label": "Cancel",
                "onClick": function() {
                    $(this).dialog('close');
                },
                "icon": "fa-times",
                "class": "btn btn-default",
                "id": "survey-close-button"
            },{
                "label": (mode==='survey-taker') ? "Launch" : "Save" ,
                "onClick": function() {
                    setTimeout(function(){
                        scope.$apply(function(){
                            if(mode==='survey-taker'){
                                scope.$emit('SurveyTakerCompleted');
                            } else{
                                scope.saveSurvey();
                            }
                        });
                    });
                },
                "icon":  (mode==='survey-taker') ? "fa-rocket" : "fa-check",
                "class": "btn btn-primary",
                "id": "survey-save-button"
            }];

            CreateDialog({
                id: target,
                title: title,
                scope: scope,
                buttons: buttons,
                width: 700,
                height: 725,
                minWidth: 400,
                onClose: function() {
                    $('#'+target).empty();
                },
                onOpen: function() {
                    Wait('stop');
                    if(mode!=="survey-taker"){
                        $('#survey-save-button').attr('ng-disabled', "survey_questions.length<1 ");
                        element = angular.element(document.getElementById('survey-save-button'));
                        $compile(element)(scope);

                    }
                    if(mode==="survey-taker"){
                        $('#survey-save-button').attr('ng-disabled',  "survey_taker_form.$invalid");
                        element = angular.element(document.getElementById('survey-save-button'));
                        $compile(element)(scope);

                    }

                },
                callback: callback
            });
        };
    }])

    .factory('EditSurvey', ['$routeParams','SchedulerInit', 'ShowSurveyModal', 'Wait', 'Rest', 'ProcessErrors', 'GetBasePath', 'GenerateForm',
            'Empty', 'AddSurvey',
    function($routeParams, SchedulerInit, ShowSurveyModal, Wait, Rest, ProcessErrors, GetBasePath, GenerateForm,
        Empty, AddSurvey) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                tempSurv = {},
                url = GetBasePath('job_templates') + id + '/survey_spec/', i;

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#survey-modal-dialog').dialog('open');
            });

            scope.resetForm();
            Wait('start');
            if(scope.mode === 'add'){
                tempSurv.survey_name = scope.survey_name;
                tempSurv.survey_description = scope.survey_description;

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
                        ProcessErrors(scope, data, status, { hdr: 'Error!',
                            msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
                    });
            }
        };
    }])

    .factory('AddSurvey', ['$location', '$routeParams', 'SchedulerInit', 'ShowSurveyModal', 'Wait',
    function($location, $routeParams, SchedulerInit, ShowSurveyModal, Wait) {
        return function(params) {
            var scope = params.scope;
                // callback= params.callback,
                // base = $location.path().replace(/^\//, '').split('/')[0],
                // url =  GetBasePath(base),
                // generator = GenerateForm,
                // form = SurveyQuestionForm;

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {

                $('#survey-modal-dialog').dialog('open');
                scope.addQuestion();

                // $('#surveyName').focus();
                // $('#question_unique_required_chbox').prop('checked' , true);
            });

            Wait('start');
            $('#form-container').empty();

            scope.resetForm();
            // generator.inject(form, { id: 'survey-modal-dialog' , mode: 'add', related: false, scope: scope, breadCrumbs: false });
            ShowSurveyModal({ title: "Add Survey", scope: scope, callback: 'DialogReady' });

            // if (scope.removeScheduleSaved) {
            //     scope.removeScheduleSaved();
            // }
            // scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
            //     Wait('stop');
            //     $('#survey-modal-dialog').dialog('close');
            //     scope.$emit('surveySaved');
            // });


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
                scope.survey_exists = false;
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
                Rest.destroy()
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
                required,
                element, choices, i, checked,
                max, min, defaultValue,

            html = "";

            // if(scope.survey_questions.length>0){
            //     $('#survey-save-button').removeAttr('disabled')
            // }

            question.index = index;

            if(!$('#question_'+question.index+':eq(0)').is('div')){
                html+='<div id="question_'+question.index+'" class="question_final row"></div>';
                $('#finalized_questions').append(html);
            }

            required = (question.required===true) ? "prepend-asterisk" : "";
            html = '<div class="col-xs-12 '+required+'"><b>'+question.question_name+'</b></div>\n';
            if(!Empty(question.question_description)){
                html += '<div class="col-xs-12 description"><i>'+question.question_description+'</i></div>\n';
            }
            // defaultValue = (question.default) ? question.default : "";

            if(question.type === 'text' ){
                defaultValue = (question.default) ? question.default : "";
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="text" placeholder="'+defaultValue+'"  class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" readonly>'+
                    '</div></div>';
            }
            if(question.type === "textarea"){
                defaultValue = (question.default) ? question.default : (question.default_textarea) ? question.default_textarea:  "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<textarea class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" rows="3" readonly>'+defaultValue+'</textarea>'+
                    '</div></div>';
            }
            if(question.type === 'multiplechoice' || question.type === "multiselect"){
                choices = question.choices.split(/\n/);
                element = (question.type==="multiselect") ? "checkbox" : 'radio';
                question.default = (question.default) ? question.default : (question.default_multiselect) ? question.default_multiselect : "" ;
                for( i = 0; i<choices.length; i++){
                    checked = (!Empty(question.default) && question.default.indexOf(choices[i])!==-1) ? "checked" : "";
                    html+='<label class="'+element+'-inline final">'+
                    '<input type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[i]+' " '+checked+' disabled>' +choices[i]+
                    '</label>';
                }

            }
            if(question.type === 'integer'){
                min = (!Empty(question.min)) ? question.min : "";
                max = (!Empty(question.max)) ? question.max : "" ;
                defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_int)) ? question.default_int : "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="number" class="final form-control" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'" readonly>'+
                    '</div></div>';

            }
            if(question.type === "float"){
                min = (!Empty(question.min)) ? question.min : "";
                max = (!Empty(question.max)) ? question.max : "" ;
                defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_float)) ? question.default_float : "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="number" class="final form-control" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'" readonly>'+
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
            element.css('opacity', 0.7);
            $compile(element)(scope);
            // var questionScope = scope.$new;

            $('#add_question_btn').show();
            $('#add_question_btn').removeAttr('disabled');
            $('#add_question_btn').focus();
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

            $('#survey-save-button').attr('disabled', 'disabled');
            $('#add_question_btn').hide();
            $('#new_question .aw-form-well').remove();
            element = $('.question_final:eq('+index+')');
            element.css('opacity', 1.0);
            element.empty();
            scope.int_min = null;
            scope.int_max = null;
            scope.float_min = null;
            scope.float_max = null;
            GenerateForm.inject(form, { id: 'question_'+index, mode: 'edit' , related: false, scope:scope, breadCrumbs: false});
            for(fld in form.fields){
                if( scope.survey_questions[index].type==='integer' && fld === 'int_options'){
                    scope.int_min = scope.survey_questions[index].min;
                    scope.int_max = scope.survey_questions[index].max;
                    // $("#int_min").val(scope.survey_questions[index].min);
                    // $("#int_max").val(scope.survey_questions[index].max);
                }
                if( scope.survey_questions[index].type==='float' && fld  === 'float_options'  ) {
                    scope.float_min = scope.survey_questions[index].min;
                    scope.float_max = scope.survey_questions[index].max;
                    // $("#float_min").val(scope.survey_questions[index].min);
                    // $("#float_max").val(scope.survey_questions[index].max);
                }
                if( fld  === 'default_int' || fld === 'default_float'){
                    $("#"+fld ).val(scope.survey_questions[index].default);
                }
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
            element.remove();
            scope.survey_questions.splice(index, 1);
            scope.reorder();
            if(scope.survey_questions.length<1){
                $('#survey-save-button').attr('disabled', 'disabled');
            }
        };
    })

    .factory('SurveyControllerInit', ['$location', 'DeleteSurvey', 'EditSurvey', 'AddSurvey', 'GenerateForm', 'SurveyQuestionForm', 'Wait', 'Alert',
            'GetBasePath', 'Rest', 'ProcessErrors' , '$compile', 'FinalizeQuestion', 'EditQuestion', 'DeleteQuestion',
        function($location, DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert,
            GetBasePath, Rest, ProcessErrors, $compile, FinalizeQuestion, EditQuestion, DeleteQuestion) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                i, url, html, element,
                form = SurveyQuestionForm;

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

                GenerateForm.inject(form, { id:'new_question', mode: 'add' , scope:scope, related: false, breadCrumbs: false});
                scope.required = true; //set the required checkbox to true via the ngmodel attached to scope.required.
                scope.int_min = null;
                scope.int_max = null;
                scope.float_min = null;
                scope.float_max = null;
            };

            scope.addNewQuestion = function(){
                // $('#add_question_btn').on("click" , function(){
                scope.addQuestion();
                $('#survey_question_question_name').focus();
                $('#add_question_btn').attr('disabled', 'disabled');
                $('#add_question_btn').hide();
                $('#survey-save-button').attr('disabled' , 'disabled');
            // });
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
            scope.cancelQuestion = function(event){
                var elementID, key;
                if(event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id==="new_question"){
                    $('#new_question .aw-form-well').remove();
                    $('#add_question_btn').show();
                    $('#add_question_btn').removeAttr('disabled');
                } else {
                    elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id;
                    key = elementID.split('_')[1];
                    $('#'+elementID).empty();
                    scope.finalizeQuestion(scope.survey_questions[key] , key);
                }


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

            scope.typeChange = function() {
                // alert('typechange');
                scope.default = null;
                scope.default_multiselect = null;
                scope.default_float = null;
                scope.default_int = null;
                scope.default_textarea = null;
                scope.int_min = null;
                scope.int_max = null;
                scope.float_min = null;
                scope.float_max = null;
            };

            scope.submitQuestion = function(){
                var form = SurveyQuestionForm,
                data = {},
                // labels={},
                // min= "min",
                // max = "max",
                fld, key, elementID;
                //generator.clearApiErrors();
                Wait('start');

                try {
                    for (fld in form.fields) {
                        if(fld==='required'){
                            data[fld] = (scope[fld]===true) ? true : false;
                        }
                        if(scope[fld]){
                            if(fld === "type"){
                                data[fld] = scope[fld].type;

                                if(scope[fld].type === 'float'){
                                    data.min = scope.float_min;
                                    data.max = scope.float_max;
                                    data.default = scope.default_float;
                                }
                                if(scope[fld].type==="integer" ){
                                    data.min = scope.int_min;
                                    data.max = scope.int_max;
                                    data.default = scope.default_int;
                                }
                            }
                            else if(fld==='default_multiselect'){
                                data.default = scope.default_multiselect;
                            }
                            else{
                                data[fld] = scope[fld];
                            }

                        }
                    }
                    Wait('stop');
                    $('#survey-save-button').removeAttr('disabled');
                    if(GenerateForm.mode === 'add'){
                        scope.survey_questions.push(data);
                        $('#new_question .aw-form-well').remove();
                        // scope.addQuestion()
                        $('#add_question_btn').show();
                        scope.finalizeQuestion(data , scope.survey_questions.length-1);
                    }
                    if(GenerateForm.mode === 'edit'){
                        elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id;
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
            scope.resetForm = function(){
                html = '<div class="row">'+
                        '<div class="col-sm-12">'+
                        '<label for="survey"><span class="label-text prepend-asterisk">Questions</span></label>'+
                        '<div id="survey_maker_question_area"></div>'+
                        '<div id="finalized_questions"></div>'+
                        '<button style="display:none" type="button" class="btn btn-sm btn-primary" id="add_question_btn" ng-click="addNewQuestion()" aw-tool-tip="Create a new question" data-placement="top" data-original-title="" title="" disabled><i class="fa fa-plus fa-lg"></i>  New Question</button>'+
                        '<div id="new_question"></div>'+
                    '</div>'+
                '</div>';
                $('#survey-modal-dialog').html(html);
                element = angular.element(document.getElementById('add_question_btn'));
                $compile(element)(scope);
            };

            scope.saveSurvey = function() {
                Wait('start');
                if(scope.mode==="add"){
                    $('#survey-modal-dialog').dialog('close');
                    scope.survey_name = "";
                    scope.survey_description = "";
                    scope.$emit('SurveySaved');
                }
                else{
                    scope.survey_name = "";
                    scope.survey_description = "";
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


