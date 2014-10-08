// /************************************
//  * Copyright (c) 2014 AnsibleWorks, Inc.
//  *
//  *
//  *  SurveyMaker.js
//  *
//  *  Controller functions for the survey maker
//  *
//  */
// /**
//  * @ngdoc function
//  * @name controllers.function:SurveyMaker
//  * @description This controller's for the survey maker page.
//  * The survey maker interacts with the job template page, and the two go hand in hand. The scenarios are:
//  * New job template - add new survey
//  * New job template - edit new survey
//  * Edit existing job template - add new survey
//  * Edit Existing job template - edit existing survey
//  *
//  * Adding a new survey to any page takes the user to the Add New Survey page
//  *                   Adding a new survey to a new job template saves the survey to session memory (navigating to survey maker forces us to save JT in memory temporarily)
//  *                   Adding a new survey to an existing job template send the survey to the API
//  *  Editing an existing survey takes the user to the Edit Survey page
//  *                  Editing a survey attached to a new job template saves the survey to session memory (saves the job template in session memory)
//  *                  Editing a survey attached to an existing job template saves the survey to the API
//  *
//  *  The variables in local memory are cleaned out whenever the user navigates to a page (other than the Survey Maker page)
// */
// 'use strict';

// function SurveyController($scope, $rootScope, $compile, $location, $log, $routeParams, SurveyMakerForm,
//     GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath,
//     ReturnToCaller, Wait, SurveyQuestionForm, Store) {


// angular.module('SurveyHelper', [ 'Utilities', 'RestServices', 'SchedulesHelper', 'SearchHelper', 'PaginationHelpers', 'ListGenerator', 'ModalDialog',
//     'GeneratorHelpers'])

//     .factory('ShowSurveyModal', ['Wait', 'CreateDialog', 'Empty', '$compile' ,
//         function(Wait, CreateDialog, Empty, $compile) {
//         return function(params) {
//             // Set modal dimensions based on viewport width

//             var scope = params.scope,
//                 callback = params.callback,
//                 mode = (params.mode) ? params.mode : "survey-maker",
//                 title = params.title,
//                 element,
//                 target = (mode==='survey-taker') ? 'password-modal' : "survey-modal-dialog",
//                 buttons = [{
//                 "label": "Cancel",
//                 "onClick": function() {
//                     $(this).dialog('close');
//                 },
//                 "icon": "fa-times",
//                 "class": "btn btn-default",
//                 "id": "survey-close-button"
//             },{
//                 "label": (mode==='survey-taker') ? "Launch" : "Save" ,
//                 "onClick": function() {
//                     setTimeout(function(){
//                         scope.$apply(function(){
//                             if(mode==='survey-taker'){
//                                 scope.$emit('SurveyTakerCompleted');
//                             } else{
//                                 scope.saveSurvey();
//                             }
//                         });
//                     });
//                 },
//                 "icon":  (mode==='survey-taker') ? "fa-rocket" : "fa-check",
//                 "class": "btn btn-primary",
//                 "id": "survey-save-button"
//             }];

//             CreateDialog({
//                 id: target,
//                 title: title,
//                 scope: scope,
//                 buttons: buttons,
//                 width: 700,
//                 height: 725,
//                 minWidth: 400,
//                 onClose: function() {
//                     $('#'+target).empty();
//                 },
//                 onOpen: function() {
//                     Wait('stop');
//                     if(mode!=="survey-taker"){
//                         $('#survey-save-button').attr('ng-disabled', "survey_questions.length<1 ");
//                         element = angular.element(document.getElementById('survey-save-button'));
//                         $compile(element)(scope);

//                     }
//                     if(mode==="survey-taker"){
//                         $('#survey-save-button').attr('ng-disabled',  "survey_taker_form.$invalid");
//                         element = angular.element(document.getElementById('survey-save-button'));
//                         $compile(element)(scope);

//                     }

//                 },
//                 callback: callback
//             });
//         };
//     }])

//     .factory('EditSurvey', ['$routeParams','SchedulerInit', 'ShowSurveyModal', 'Wait', 'Rest', 'ProcessErrors', 'GetBasePath', 'GenerateForm', 'SurveyMakerForm',
//             'Empty', 'AddSurvey',
//     function($routeParams, SchedulerInit, ShowSurveyModal, Wait, Rest, ProcessErrors, GetBasePath, GenerateForm,SurveyMakerForm,
//         Empty, AddSurvey) {
//         return function(params) {
//             var scope = params.scope,
//                 id = params.id,
//                 // callback = params.callback,
//                 tempSurv = {},
//                 generator = GenerateForm,
//                 form = SurveyMakerForm,
//                 // labels={
//                 //     "type": "Type",
//                 //     "question_name": "Question Text",
//                 //     "question_description": "Question Description",
//                 //     "variable": "Answer Varaible Name",
//                 //     "choices": "Choices",
//                 //     "min": "Min",
//                 //     "max": "Max",
//                 //     "required": "Required",
//                 //     "default": "Default Answer"
//                 // },
//                 url = GetBasePath('job_templates') + id + '/survey_spec/', i;

//             if (scope.removeDialogReady) {
//                 scope.removeDialogReady();
//             }
//             scope.removeDialogReady = scope.$on('DialogReady', function() {
//                 $('#survey-modal-dialog').dialog('open');
//             });


//             Wait('start');
//             if(scope.mode === 'add'){
//                 tempSurv.survey_name = scope.survey_name;
//                 tempSurv.survey_description = scope.survey_description;
//                 generator.inject(form, { id: 'survey-modal-dialog' , mode: 'edit', related: false, scope: scope, breadCrumbs: false });

//                 ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });

//                 scope.survey_name = tempSurv.survey_name;
//                 scope.survey_description = tempSurv.survey_description;
//                 // scope.survey_questions = data.spec;
//                 for(i=0; i<scope.survey_questions.length; i++){
//                     scope.finalizeQuestion(scope.survey_questions[i], i);
//                 }
//             }
//             else{
//                 // Get the existing record
//                 Rest.setUrl(url);
//                 Rest.get()
//                     .success(function (data) {
//                             if(!Empty(data)){
//                                 generator.inject(form, { id: 'survey-modal-dialog' , mode: 'edit', related: false, scope: scope, breadCrumbs: false });
//                                 ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });

//                                 scope.survey_name = data.name;
//                                 scope.survey_description = data.description;
//                                 scope.survey_questions = data.spec;
//                                 for(i=0; i<scope.survey_questions.length; i++){
//                                     scope.finalizeQuestion(scope.survey_questions[i], i);
//                                 }
//                                 // scope.addQuestion();
//                                 Wait('stop');
//                             } else {
//                                 AddSurvey({
//                                     scope: scope
//                                 });
//                             }

//                         })
//                     .error(function (data, status) {
//                         ProcessErrors(scope, data, status, form, { hdr: 'Error!',
//                             msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
//                     });
//             }
//         };
//     }])

//     .factory('AddSurvey', ['$location', '$routeParams', 'SchedulerInit', 'ShowSurveyModal', 'Wait', 'GetBasePath', 'Empty',
//         'SchedulePost', 'GenerateForm', 'SurveyMakerForm',
//     function($location, $routeParams, SchedulerInit, ShowSurveyModal, Wait, GetBasePath, Empty,
//         SchedulePost, GenerateForm, SurveyMakerForm) {
//         return function(params) {
//             var scope = params.scope,
//                 // callback= params.callback,
//                 // base = $location.path().replace(/^\//, '').split('/')[0],
//                 // url =  GetBasePath(base),
//                 generator = GenerateForm,
//                 form = SurveyMakerForm;

//             if (scope.removeDialogReady) {
//                 scope.removeDialogReady();
//             }
//             scope.removeDialogReady = scope.$on('DialogReady', function() {
//                 scope.addQuestion();
//                 $('#survey-modal-dialog').dialog('open');
//                 // $('#surveyName').focus();
//                 // $('#question_unique_required_chbox').prop('checked' , true);
//             });

//             Wait('start');
//             $('#form-container').empty();


//             generator.inject(form, { id: 'survey-modal-dialog' , mode: 'add', related: false, scope: scope, breadCrumbs: false });
//             ShowSurveyModal({ title: "Add Survey", scope: scope, callback: 'DialogReady' });

//             // if (scope.removeScheduleSaved) {
//             //     scope.removeScheduleSaved();
//             // }
//             // scope.removeScheduleSaved = scope.$on('ScheduleSaved', function() {
//             //     Wait('stop');
//             //     $('#survey-modal-dialog').dialog('close');
//             //     scope.$emit('surveySaved');
//             // });


//         };
//     }])

//     /**
//      * Delete a survey. Prompts user to confirm delete
//      *
//      * DeleteSurvey({
//      *     scope:       $scope containing list of survey form fields
//      *     id:          id of job template that survey is attached to
//      *     callback:    $scope.$emit label to call when delete is completed
//      * })
//      *
//      */
//     .factory('DeleteSurvey', ['GetBasePath','Rest', 'Wait', 'ProcessErrors',
//     function(GetBasePath, Rest, Wait, ProcessErrors) {
//         return function(params) {

//             var scope = params.scope,
//                 id = params.id,
//                 // callback = params.callback,
//                 url;


//             if (scope.removeSurveyDeleted) {
//                 scope.removeSurveyDeleted();
//             }
//             scope.$on('SurveyDeleted', function(){
//                 scope.survey_name = "";
//                 scope.survey_description = "";
//                 scope.survey_questions = [];
//                 Wait('stop');
//                 scope.survey_exists = false;
//                 $('#job_templates_delete_survey_btn').hide();
//                 $('#job_templates_edit_survey_btn').hide();
//                 $('#job_templates_create_survey_btn').show();
//             });


//             Wait('start');

//             if(scope.mode==="add"){
//                 scope.$emit("SurveyDeleted");

//             } else {
//                 url = GetBasePath('job_templates')+ id + '/survey_spec/';

//                 Rest.setUrl(url);
//                 Rest.post({})
//                     .success(function () {
//                         scope.$emit("SurveyDeleted");

//                     })
//                     .error(function (data, status) {
//                         ProcessErrors(scope, data, status, { hdr: 'Error!',
//                             msg: 'Failed to add new survey. Post returned status: ' + status });
//                     });
//             }
//         };
//     }])

// /**
//      * Takes a finalized question and displays it on the survey maker page
//      *
//      * FinalizeQuestion({
//      *     scope:       $scope containing list of survey form fields
//      *     question: question object that was submitted by the question form
//      *     id:          id of job template that survey is attached to
//      *     callback:    $scope.$emit label to call when delete is completed
//      * })
//      *
//      */
//     .factory('FinalizeQuestion', ['GetBasePath','Rest', 'Wait', 'ProcessErrors', '$compile', 'Empty',
//     function(GetBasePath, Rest, Wait, ProcessErrors, $compile, Empty) {
//         return function(params) {

//             var scope = params.scope,
//                 // id = params.id,
//                 question = params.question,
//                 index = params.index,
//                 required,
//                 element, choices, i, checked,
//                 max, min, defaultValue, numberValidation,

//             html = "";

//             // if(scope.survey_questions.length>0){
//             //     $('#survey-save-button').removeAttr('disabled')
//             // }

//             question.index = index;

//             if(!$('#question_'+question.index+':eq(0)').is('div')){
//                 html+='<div id="question_'+question.index+'" class="question_final row"></div>';
//                 $('#finalized_questions').append(html);
//             }

//             required = (question.required===true) ? "prepend-asterisk" : "";
//             html = '<div class="col-xs-12 '+required+'"><b>'+question.question_name+'</b></div>\n';
//             if(!Empty(question.question_description)){
//                 html += '<div class="col-xs-12 description"><i>'+question.question_description+'</i></div>\n';
//             }
//             defaultValue = (question.default) ? question.default : "";

//             if(question.type === 'text' ){
//                 html+='<div class="row">'+
//                     '<div class="col-xs-8">'+
//                     '<input type="text" placeholder="'+defaultValue+'"  class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" readonly>'+
//                     '</div></div>';
//             }
//             if(question.type === "textarea"){
//                 html+='<div class="row">'+
//                     '<div class="col-xs-8">'+
//                     '<textarea class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" rows="3" readonly>'+defaultValue+'</textarea>'+
//                     '</div></div>';
//             }
//             if(question.type === 'multiplechoice' || question.type === "multiselect"){
//                 choices = question.choices.split(/\n/);
//                 element = (question.type==="multiselect") ? "checkbox" : 'radio';

//                 for( i = 0; i<choices.length; i++){
//                     checked = (!Empty(question.default) && question.default.indexOf(choices[i])!==-1) ? "checked" : "";
//                     html+='<label class="'+element+'-inline final">'+
//                     '<input type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[i]+' " '+checked+' disabled>' +choices[i]+
//                     '</label>';
//                 }

//             }
//             if(question.type === 'integer' || question.type === "float"){
//                 min = (question.min) ? question.min : "";
//                 max = (question.max) ? question.max : "" ;
//                 numberValidation = (question.type==="integer") ? "integer" : 'float';
//                 html+='<div class="row">'+
//                     '<div class="col-xs-8">'+
//                     '<input type="number" class="final" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'" readonly '+numberValidation+'>'+
//                     '</div></div>';

//             }
//             html += '<div class="col-xs-12 text-right" id="question_actions">';
//             html += '<a id="edit-question_'+question.index+'" data-placement="top" aw-tool-tip="Edit question" data-original-title="" title=""><i class="fa fa-pencil"></i> </a>';
//             html += '<a id="delete-question_'+question.index+'" data-placement="top" aw-tool-tip="Delete question" data-original-title="" title=""><i class="fa fa-trash-o"></i> </a>';
//             html += '<a id="question-up_'+question.index+'" data-placement="top" aw-tool-tip="Move up" data-original-title="" title=""><i class="fa fa-arrow-up"></i> </a>';
//             html += '<a id="question-down_'+question.index+'" data-placement="top" aw-tool-tip="Move down" data-original-title="" title=""><i class="fa fa-arrow-down"></i> </a>';
//             html+='</div></div>';

//             $('#question_'+question.index).append(html);

//             element = angular.element(document.getElementById('question_'+question.index));
//             // element.html(html);
//             element.css('opacity', 0.7);
//             $compile(element)(scope);
//             // var questionScope = scope.$new;

//             $('#add_question_btn').show();
//             $('#add_question_btn').removeAttr('disabled');
//             $('#add_question_btn').focus();
//             $('#survey_maker_save_btn').removeAttr('disabled');

//             $('#delete-question_'+question.index+'').on('click', function($event){
//                 scope.deleteQuestion($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
//             });
//             $('#edit-question_'+question.index+'').on('click', function($event){
//                 scope.editQuestion($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
//             });
//             $('#question-up_'+question.index+'').on('click', function($event){
//                 scope.questionUp($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
//             });
//             $('#question-down_'+question.index+'').on('click', function($event){
//                 scope.questionDown($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
//             });
//         };
//     }])

//  .factory('SurveyTakerQuestion', ['GetBasePath','Rest', 'Wait', 'ProcessErrors', '$compile', 'Empty',
//     function(GetBasePath, Rest, Wait, ProcessErrors, $compile, Empty) {
//         return function(params) {

//             var scope = params.scope,
//                 // id = params.id,
//                 question = params.question,
//                 index = params.index,
//                 requiredAsterisk,
//                 requiredClasses,
//                 element, choices, i, checked,
//                 max, min, defaultValue, numberValidation

//             html = "";

//             // if(scope.survey_questions.length>0){
//             //     $('#survey-save-button').removeAttr('disabled')
//             // }

//             question.index = index;
//             question[question.variable] = question.default;
//             scope[question.variable] = question.default;


//             if(!$('#question_'+question.index+':eq(0)').is('div')){
//                 html+='<div id="question_'+question.index+'" class="survey_taker_question_final row"></div>';
//                 $('#survey_taker_finalized_questions').append(html);
//             }

//             requiredAsterisk = (question.required===true) ? "prepend-asterisk" : "";
//             requiredClasses = (question.required===true) ? "ng-pristine ng-invalid-required ng-invalid" : "";

//             html = '<div class="col-xs-12 '+requiredAsterisk+'"><b>'+question.question_name+'</b></div>\n';
//             if(!Empty(question.question_description)){
//                 html += '<div class="col-xs-12 description"><i>'+question.question_description+'</i></div>\n';
//             }
//             defaultValue = (question.default) ? question.default : "";

//             if(question.type === 'text' ){
//                 html+='<div class="row">'+
//                     '<div class="col-xs-8">'+
//                     '<input type="text" ng-model="'+question.variable+'" '+         //placeholder="'+defaultValue+'"
//                             'class="form-control '+requiredClasses+' final" required="" >'+
//                     '</div></div>';
//             }
//             if(question.type === "textarea"){
//                 html+='<div class="row">'+
//                     '<div class="col-xs-8">'+
//                     '<textarea ng-model="'+question.variable+'" class="form-control '+requiredClasses+' final" required="" rows="3" >'+//defaultValue+
//                             '</textarea>'+
//                     '</div></div>';
//             }
//             if(question.type === 'multiplechoice' || question.type === "multiselect"){
//                 choices = question.choices.split(/\n/);
//                 element = (question.type==="multiselect") ? "checkbox" : 'radio';

//                 for( i = 0; i<choices.length; i++){
//                     checked = (!Empty(question.default) && question.default.indexOf(choices[i].trim())!==-1) ? "checked" : "";
//                     html+='<label class="'+element+'-inline  final">'+
//                     '<input type="'+element+'" name="'+question.variable+ ' " id="" value=" '+choices[i]+' " '+checked+' >' +choices[i]+
//                     '</label>';
//                 }

//             }
//             if(question.type === 'integer' || question.type === "float"){
//                 min = (question.min) ? question.min : "";
//                 max = (question.max) ? question.max : "" ;
//                 numberValidation = (question.type==="integer") ? "integer" : 'float';
//                 html+='<div class="row">'+
//                     '<div class="col-xs-8">'+
//                     '<input type="number" class="final" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'">'+
//                     '</div></div>';

//             }
//             $('#question_'+question.index).append(html);

//             element = angular.element(document.getElementById('question_'+question.index));
//             $compile(element)(scope);

//         };
//     }])

//      .factory('EditQuestion', ['GetBasePath','Rest', 'Wait', 'ProcessErrors', '$compile', 'GenerateForm', 'SurveyQuestionForm',
//     function(GetBasePath, Rest, Wait, ProcessErrors, $compile, GenerateForm, SurveyQuestionForm) {
//         return function(params) {

//             var scope = params.scope,
//                 index = params.index,
//                 element, fld, i,
//                 form = SurveyQuestionForm;

//             $('#add_question_btn').hide();
//             $('#new_question .aw-form-well').remove();
//             element = $('.question_final:eq('+index+')');
//             element.css('opacity', 1.0);
//             element.empty();
//             // $('#new_question .aw-form-well').remove();
//             GenerateForm.inject(form, { id: 'question_'+index, mode: 'edit' , scope:scope, breadCrumbs: false});
//             for(fld in form.fields){
//                 if( fld  === 'answer_options_number'){
//                     $('#answer_min').val(scope.survey_questions[index].min);
//                     $('#answer_max').val(scope.survey_questions[index].max);
//                 }
//                 if( fld  === 'default_int' || fld === 'default_float'){
//                     $("#"+fld ).val(scope.survey_questions[index].default);
//                 }
//                 if(form.fields[fld].type === 'select'){
//                     for (i = 0; i < scope.answer_types.length; i++) {
//                         if (scope.survey_questions[index][fld] === scope.answer_types[i].type) {
//                             scope[fld] = scope.answer_types[i];
//                         }
//                     }
//                 } else {
//                     scope[fld] = scope.survey_questions[index][fld];
//                 }
//             }
//         };
//     }])

//      .factory('DeleteQuestion' ,
//     function() {
//         return function(params) {

//             var scope = params.scope,
//                 index = params.index,
//                 element;

//             element = $('.question_final:eq('+index+')');
//             element.remove();
//             scope.survey_questions.splice(index, 1);
//             scope.reorder();
//             if(scope.survey_questions.length<1){
//                 $('#survey-save-button').attr('disabled', 'disabled');
//             }
//         };
//     })

//     .factory('SurveyControllerInit', ['$location', 'DeleteSurvey', 'EditSurvey', 'AddSurvey', 'GenerateForm', 'SurveyQuestionForm', 'Wait', 'Alert',
//             'GetBasePath', 'Rest', 'ProcessErrors' , '$compile', 'FinalizeQuestion', 'EditQuestion', 'DeleteQuestion', 'SurveyTakerQuestion',
//         function($location, DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert,
//             GetBasePath, Rest, ProcessErrors, $compile, FinalizeQuestion, EditQuestion, DeleteQuestion, SurveyTakerQuestion) {
//         return function(params) {
//             var scope = params.scope,
//                 id = params.id,
//                 i, url;

//             scope.survey_questions = [];
//             scope.answer_types=[
//                 {name: 'Text' , type: 'text'},
//                 {name: 'Textarea', type: 'textarea'},
//                 {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
//                 {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
//                 {name: 'Integer', type: 'integer'},
//                 {name: 'Float', type: 'float'}
//             ];

//             scope.deleteSurvey = function() {
//                 DeleteSurvey({
//                     scope: scope,
//                     id: id,
//                     // callback: 'SchedulesRefresh'
//                 });
//             };

//             scope.editSurvey = function() {
//                 EditSurvey({
//                     scope: scope,
//                     id: id,
//                     // callback: 'SchedulesRefresh'
//                 });
//             };

//             scope.addSurvey = function() {
//                 AddSurvey({
//                     scope: scope,
//                     // callback: 'SchedulesRefresh'
//                 });
//             };
//             scope.addQuestion = function(){
//                 GenerateForm.inject(SurveyQuestionForm, { id:'new_question', mode: 'add' , scope:scope, breadCrumbs: false});
//                 scope.required = true; //set the required checkbox to true via the ngmodel attached to scope.required.

//             };

//             scope.addNewQuestion = function(){
//                 // $('#add_question_btn').on("click" , function(){
//                 scope.addQuestion();
//                 $('#survey_question_question_name').focus();
//                 $('#add_question_btn').attr('disabled', 'disabled');
//                 $('#add_question_btn').hide();
//             // });
//             };
//             scope.editQuestion = function(index){
//                 EditQuestion({
//                     index: index,
//                     scope: scope
//                 });
//             };

//             scope.deleteQuestion = function(index){
//                 DeleteQuestion({
//                     index:index,
//                     scope: scope
//                 });
//             };

//             scope.questionUp = function(index){
//                 var animating = false,
//                     clickedDiv = $('#question_'+index),
//                     prevDiv = clickedDiv.prev(),
//                     distance = clickedDiv.outerHeight();

//                 if (animating) {
//                     return;
//                 }

//                 if (prevDiv.length) {
//                     animating = true;
//                     $.when(clickedDiv.animate({
//                         top: -distance
//                     }, 600),
//                     prevDiv.animate({
//                         top: distance
//                     }, 600)).done(function () {
//                         prevDiv.css('top', '0px');
//                         clickedDiv.css('top', '0px');
//                         clickedDiv.insertBefore(prevDiv);
//                         animating = false;
//                         i = scope.survey_questions[index];
//                         scope.survey_questions[index] = scope.survey_questions[index-1];
//                         scope.survey_questions[index-1] = i;
//                         scope.reorder();
//                     });
//                 }
//             };

//             scope.questionDown = function(index){
//                 var clickedDiv = $('#question_'+index),
//                     nextDiv = clickedDiv.next(),
//                     distance = clickedDiv.outerHeight(),
//                     animating = false;

//                 if (animating) {
//                     return;
//                 }

//                 if (nextDiv.length) {
//                     animating = true;
//                     $.when(clickedDiv.animate({
//                         top: distance
//                     }, 600),
//                     nextDiv.animate({
//                         top: -distance
//                     }, 600)).done(function () {
//                         nextDiv.css('top', '0px');
//                         clickedDiv.css('top', '0px');
//                         nextDiv.insertBefore(clickedDiv);
//                         animating = false;
//                         i = scope.survey_questions[index];
//                         scope.survey_questions[index] = scope.survey_questions[Number(index)+1];
//                         scope.survey_questions[Number(index)+1] = i;
//                         scope.reorder();
//                     });
//                 }
//             };

//             scope.reorder = function(){
//                 for(i=0; i<scope.survey_questions.length; i++){
//                     scope.survey_questions[i].index=i;
//                     $('.question_final:eq('+i+')').attr('id', 'question_'+i);
//                     // $('#delete-question_'+question.index+'')
//                 }
//             };

//             scope.surveyTakerQuestion= function(data, index){
//                 SurveyTakerQuestion({
//                     scope: scope,
//                     question: data,
//                     id: id,
//                     index: index
//                     //callback?
//                 });
//             };

//             scope.finalizeQuestion= function(data, index){
//                 FinalizeQuestion({
//                     scope: scope,
//                     question: data,
//                     id: id,
//                     index: index
//                     //callback?
//                 });
//             };


//             scope.submitQuestion = function(){
//                 var form = SurveyQuestionForm,
//                 data = {},
//                 labels={},
//                 min= "min",
//                 max = "max",
//                 fld, key, elementID;
//                 //generator.clearApiErrors();
//                 Wait('start');

//                 try {
//                     for (fld in form.fields) {
//                         if(fld==='required'){
//                             data[fld] = (scope[fld]===true) ? true : false;
//                         }
//                         if(scope[fld]){
//                             if(fld === "type"){
//                                 data[fld] = scope[fld].type;
//                                 // if(scope[fld].type==="textarea"){
//                                 //     data["default"] = scope.default_textarea;
//                                 // }
//                                 // if(scope[fld].type==="multiselect"){
//                                 //     data["default"] = scope.default_multiselect;
//                                 // }
//                                 if(scope[fld].type === 'float'){
//                                     data[min] = $('#answer_min').val();
//                                     data[max] = $('#answer_max').val();
//                                     labels[min]= "Min";
//                                     labels[max]= "Max";
//                                     // data["default"] = $('#default_float').val(); //scope.default_float;
//                                 }
//                                 if(scope[fld].type==="integer" ){
//                                     data[min] = $('#answer_min').val();
//                                     data[max] = $('#answer_max').val();
//                                     labels[min]= "Min";
//                                     labels[max]= "Max";
//                                     // data["default"] = $('#default_int').val(); //scope.default_int;
//                                 }
//                             }
//                             else{
//                                 data[fld] = scope[fld];
//                                 if( fld === 'default_int' || fld === 'default_float' ){
//                                     data['default'] = $('#'+fld).val();
//                                 }
//                                 if(fld==="default_textarea" ){
//                                     data['default'] = scope.default_textarea;
//                                 }
//                                 if(fld==="default_multiselect"){
//                                     data['default'] = scope.default_multiselect;
//                                 }
//                             }
//                             labels[fld] = form.fields[fld].label;
//                         }
//                     }
//                     Wait('stop');

//                     if(GenerateForm.mode === 'add'){
//                         scope.survey_questions.push(data);
//                         $('#new_question .aw-form-well').remove();
//                         // scope.addQuestion()
//                         $('#add_question_btn').show();
//                         scope.finalizeQuestion(data , scope.survey_questions.length-1);
//                     }
//                     if(GenerateForm.mode === 'edit'){
//                         elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.id;
//                         key = elementID.split('_')[1];
//                         scope.survey_questions[key] = data;
//                         $('#'+elementID).empty();
//                         scope.finalizeQuestion(data , key);
//                     }



//                 } catch (err) {
//                     Wait('stop');
//                     Alert("Error", "Error parsing extra variables. Parser returned: " + err);
//                 }
//             };

//             scope.saveSurvey = function() {
//                 Wait('start');
//                 if(scope.mode==="add"){
//                     $('#survey-modal-dialog').dialog('close');
//                     scope.survey_name = "";
//                     scope.survey_description = "";
//                     scope.$emit('SurveySaved');
//                 }
//                 else{
//                     scope.survey_name = "";
//                     scope.survey_description = "";
//                     url = GetBasePath('job_templates') + id + '/survey_spec/';
//                     Rest.setUrl(url);
//                     Rest.post({ name: scope.survey_name, description: scope.survey_description, spec: scope.survey_questions })
//                         .success(function () {
//                             // Wait('stop');
//                             $('#survey-modal-dialog').dialog('close');
//                             scope.$emit('SurveySaved');
//                         })
//                         .error(function (data, status) {
//                             ProcessErrors(scope, data, status, { hdr: 'Error!',
//                                 msg: 'Failed to add new survey. Post returned status: ' + status });
//                         });
//                 }
//             };

//         };
//     }]);




// SurveyMakerEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'SurveyMakerForm',
//     'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'Wait', 'SurveyQuestionForm', 'Store'
// ];

//     // ClearScope();

// //     // Inject dynamic view
// //     var generator = GenerateForm,
// //         form = SurveyMakerForm,
// //         base = $location.path().replace(/^\//, '').split('/')[0],
// //         id = $location.path().replace(/^\//, '').split('/')[1];

// //     $scope.survey_questions=[];
// //     $scope.Store = Store;
// //     $scope.answer_types=[
// //         {name: 'Text' , type: 'text'},
// //         {name: 'Textarea', type: 'textarea'},
// //         {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
// //         {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
// //         {name: 'JSON', type: 'json'},
// //         {name: 'Integer', type: 'integer'},
// //         {name: 'Float', type: 'number'}
// //     ];


// //     generator.inject(form, { mode: 'add', related: false, scope: $scope});
// //     generator.reset();
// //     // LoadBreadCrumbs();
// //     // LoadBreadCrumbs({
// //     //                 path: '/job_templates/' + id + '/survey',
// //     //                 title: 'jared rocks', // $scope.job_id + ' - ', //+ data.summary_fields.job_template.name,
// //     //                 altPath:  '/job_templates/' + id + '/survey',
// //     //             });

// //     $scope.addQuestion = function(){

// //         GenerateForm.inject(SurveyQuestionForm, {mode:'modal', id:'new_question', scope:$scope, breadCrumbs: false});
// //     };
// //     $scope.addQuestion();

// // // $('#question_shadow').mouseenter(function(){
// // //     $('#question_shadow').css({
// // //         "opacity": "1",
// // //         "border": "1px solid",
// // //         "border-color": "rgb(204,204,204)",
// // //         "border-radius": "4px"
// // //     });
// // //     $('#question_add_btn').show();
// // // });

// // // $('#question_shadow').mouseleave(function(){
// // //     $('#question_shadow').css({
// // //         "opacity": ".4",
// // //         "border": "1px dashed",
// // //         "border-color": "rgb(204,204,204)",
// // //         "border-radius": "4px"
// // //     });
// // //     $('#question_add_btn').hide();
// // // })


// //     // $('#question_shadow').on("click" , function(){
// //     //     // var survey_width = $('#survey_maker_question_area').width()-10,
// //     //     // html = "";

// //     //     // $('#add_question_btn').attr('disabled', 'disabled')
// //     //     // $('#survey_maker_question_area').append(html);
// //     //     addQuestion();
// //     //     $('#question_shadow').hide();
// //     //     $('#question_shadow').css({
// //     //         "opacity": ".4",
// //     //         "border": "1px dashed",
// //     //         "border-color": "rgb(204,204,204)",
// //     //         "border-radius": "4px"
// //     //     });
// //     // });
// //     $scope.finalizeQuestion= function(data, labels){
// //         var key,
// //         html = '<div class="question_final row">';

// //         for (key in data) {
// //             html+='<div class="col-xs-6"><label for="question_text"><span class="label-text">'+labels[key] +':  </span></label>'+data[key]+'</div>\n';
// //         }

// //         html+='</div>';

// //         $('#finalized_questions').before(html);
// //         $('#add_question_btn').show();
// //         $('#add_question_btn').removeAttr('disabled');
// //         $('#survey_maker_save_btn').removeAttr('disabled');
// //     };

// //     $('#add_question_btn').on("click" , function(){
// //             $scope.addQuestion();
// //             $('#add_question_btn').attr('disabled', 'disabled');
// //         });

// //     $scope.submitQuestion = function(){
// //         var form = SurveyQuestionForm,
// //         data = {},
// //         labels={},
// //         min= "min",
// //         max = "max",
// //         fld;
// //         //generator.clearApiErrors();
// //         Wait('start');

// //         try {
// //             for (fld in form.fields) {
// //                 if($scope[fld]){
// //                     if(fld === "type"){
// //                         data[fld] = $scope[fld].type;
// //                         if($scope[fld].type==="integer" || $scope[fld].type==="float"){
// //                             data[min] = $('#answer_min').val();
// //                             data[max] = $('#answer_max').val();
// //                             labels[min]= "Min";
// //                             labels[max]= "Max";
// //                         }
// //                     }
// //                     else{
// //                         data[fld] = $scope[fld];
// //                     }
// //                     labels[fld] = form.fields[fld].label;
// //                 }
// //             }
// //             Wait('stop');
// //             $scope.survey_questions.push(data);
// //             $('#new_question .aw-form-well').remove();
// //             // for(fld in form.fields){
// //             //     $scope[fld] = '';
// //             // }
// //             $scope.finalizeQuestion(data , labels);

// //         } catch (err) {
// //             Wait('stop');
// //             Alert("Error", "Error parsing extra variables. Parser returned: " + err);
// //         }
// //     };

// //     $scope.formSave = function () {
// //         generator.clearApiErrors();
// //         Wait('start');
// //         var url;
// //         if(!$scope.Store("survey_for_new_job_template") && $scope.Store("survey_for_new_job_template")!==false){
// //             $scope.Store('survey_for_new_job_template', {
// //                 // survey_created: true,
// //                 name: $scope.survey_name,
// //                 description: $scope.survey_description,
// //                 spec:$scope.survey_questions
// //             });
// //             Wait('stop');
// //             $location.path("/job_templates/add/");
// //         }
// //         else {
// //             url = GetBasePath(base)+ id + '/survey_spec/';

// //             Rest.setUrl(url);
// //             Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec:$scope.survey_questions })
// //                 .success(function () {
// //                     Wait('stop');
// //                     $location.path("/job_templates/"+id);
// //                 })
// //                 .error(function (data, status) {
// //                     ProcessErrors($scope, data, status, form, { hdr: 'Error!',
// //                         msg: 'Failed to add new survey. Post returned status: ' + status });
// //                 });
// //         }
// //     };

// //     // Save
// //     $scope.formSave = function () {
// //         generator.clearApiErrors();
// //         Wait('start');
// //         if($scope.Store("saved_job_template_for_survey")){
// //             $scope.Store('survey_for_new_job_template', {
// //                 // survey_created: true,
// //                 name: $scope.survey_name,
// //                 description: $scope.survey_description,
// //                 spec:$scope.survey_questions
// //             });
// //             Wait('stop');
// //             $location.path("/job_templates/add/");
// //         }
// //         else{
// //             var url = GetBasePath(base)+ id + '/survey_spec/';
// //             Rest.setUrl(url);
// //             Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec:$scope.survey_questions })
// //                 .success(function () {
// //                     Wait('stop');
// //                     $location.path("/job_templates/"+id);
// //                 })
// //                 .error(function (data, status) {
// //                     ProcessErrors($scope, data, status, form, { hdr: 'Error!',
// //                         msg: 'Failed to add new survey. Post returned status: ' + status });
// //                 });
// //         }

// //     };

// //     // Cancel
// //     $scope.formReset = function () {
// //         $rootScope.flashMessage = null;
// //         generator.reset();
// //     };
// // }

// // SurveyMakerAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'SurveyMakerForm',
// //     'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'Wait', 'SurveyQuestionForm', 'Store'
// // ];

// // function SurveyMakerEdit($scope, $rootScope, $compile, $location, $log, $routeParams, SurveyMakerForm,
// //     GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath,
// //     ReturnToCaller, Wait, SurveyQuestionForm, Store) {

// //     ClearScope();

// //     // Inject dynamic view
// //     var generator = GenerateForm,
// //         form = SurveyMakerForm,
// //         base = $location.path().replace(/^\//, '').split('/')[0],
// //         id = $location.path().replace(/^\//, '').split('/')[1],
// //         i, data;

// //     $scope.survey_questions=[];

// //     $scope.answer_types=[
// //         {name: 'Text' , type: 'text'},
// //         {name: 'Textarea', type: 'textarea'},
// //         {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
// //         {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
// //         {name: 'JSON', type: 'json'},
// //         {name: 'Integer', type: 'integer'},
// //         {name: 'Float', type: 'number'}
// //     ];

// //     $scope.Store = Store;

// //     generator.inject(form, { mode: 'edit', related: false, scope: $scope});
// //     generator.reset();
// //     // LoadBreadCrumbs();
// //     // LoadBreadCrumbs({
// //     //                 path: '/job_templates/' + id + '/survey',
// //     //                 title: 'jared rocks', // $scope.job_id + ' - ', //+ data.summary_fields.job_template.name,
// //     //                 altPath:  '/job_templates/' + id + '/survey',
// //     //             });

// //     $scope.addQuestion = function(){

// //         GenerateForm.inject(SurveyQuestionForm, {mode:'add', id:'new_question', scope:$scope, breadCrumbs: false});
// //     };
// //     // $scope.addQuestion();

// // // $('#question_shadow').mouseenter(function(){
// // //     $('#question_shadow').css({
// // //         "opacity": "1",
// // //         "border": "1px solid",
// // //         "border-color": "rgb(204,204,204)",
// // //         "border-radius": "4px"
// // //     });
// // //     $('#question_add_btn').show();
// // // });

// // // $('#question_shadow').mouseleave(function(){
// // //     $('#question_shadow').css({
// // //         "opacity": ".4",
// // //         "border": "1px dashed",
// // //         "border-color": "rgb(204,204,204)",
// // //         "border-radius": "4px"
// // //     });
// // //     $('#question_add_btn').hide();
// // // })


// //     // $('#question_shadow').on("click" , function(){
// //     //     // var survey_width = $('#survey_maker_question_area').width()-10,
// //     //     // html = "";

// //     //     // $('#add_question_btn').attr('disabled', 'disabled')
// //     //     // $('#survey_maker_question_area').append(html);
// //     //     addQuestion();
// //     //     $('#question_shadow').hide();
// //     //     $('#question_shadow').css({
// //     //         "opacity": ".4",
// //     //         "border": "1px dashed",
// //     //         "border-color": "rgb(204,204,204)",
// //     //         "border-radius": "4px"
// //     //     });
// //     // });
// //     $scope.finalizeQuestion= function(data){
// //         var key,
// //         labels={
// //             "type": "Type",
// //             "question_name": "Question Text",
// //             "question_description": "Question Description",
// //             "variable": "Answer Varaible Name",
// //             "choices": "Choices",
// //             "min": "Min",
// //             "max": "Max",
// //             "required": "Required",
// //             "default": "Default Answer"
// //         },
// //         html = '<div class="question_final row">';

// //         for (key in data) {
// //             html+='<div class="col-xs-6"><label for="question_text"><span class="label-text">'+labels[key] +':  </span></label>'+data[key]+'</div>\n';
// //         }

// //         html+='</div>';

// //         $('#finalized_questions').before(html);
// //         $('#add_question_btn').show();
// //         $('#add_question_btn').removeAttr('disabled');
// //         $('#survey_maker_save_btn').removeAttr('disabled');
// //     };

// //     $('#add_question_btn').on("click" , function(){
// //             $scope.addQuestion();
// //             $('#add_question_btn').attr('disabled', 'disabled');
// //         });

// //     Wait('start');

// //     if($scope.Store("saved_job_template_for_survey") && $scope.Store("saved_job_template_for_survey").editing_survey===true){
// //         data = $scope.Store("survey_for_new_job_template");
// //         $scope.survey_name = data.name;
// //         $scope.survey_description = data.description;
// //         $scope.survey_questions = data.spec;
// //         for(i=0; i<$scope.survey_questions.length; i++){
// //             $scope.finalizeQuestion($scope.survey_questions[i]);
// //         }
// //         Wait('stop');
// //     }
// //     else{
// //         Rest.setUrl(GetBasePath(base)+ id + '/survey_spec/');
// //         Rest.get()
// //             .success(function (data) {
// //                     var i;
// //                     $scope.survey_name = data.name;
// //                     $scope.survey_description = data.description;
// //                     $scope.survey_questions = data.spec;
// //                     for(i=0; i<$scope.survey_questions.length; i++){
// //                         $scope.finalizeQuestion($scope.survey_questions[i]);
// //                     }
// //                     Wait('stop');
// //                 // LoadBreadCrumbs({ path: '/organizations/' + id, title: data.name });
// //                 // for (fld in form.fields) {
// //                 //     if (data[fld]) {
// //                 //         $scope[fld] = data[fld];
// //                 //         master[fld] = data[fld];
// //                 //     }
// //                 // }

// //                 // related = data.related;
// //                 // for (set in form.related) {
// //                 //     if (related[set]) {
// //                 //         relatedSets[set] = {
// //                 //             url: related[set],
// //                 //             iterator: form.related[set].iterator
// //                 //         };
// //                 //     }
// //                 // }

// //                 // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
// //                 // RelatedSearchInit({ scope: $scope, form: form, relatedSets: relatedSets });
// //                 // RelatedPaginateInit({ scope: $scope, relatedSets: relatedSets });
// //                 // $scope.$emit('organizationLoaded');
// //                 })
// //             .error(function (data, status) {
// //                 ProcessErrors($scope, data, status, form, { hdr: 'Error!',
// //                     msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
// //             });
// //     }
// //     $scope.submitQuestion = function(){
// //         var form = SurveyQuestionForm,
// //         data = {},
// //         labels={},
// //         min= "min",
// //         max = "max",
// //         fld;
// //         //generator.clearApiErrors();
// //         Wait('start');

// //         try {
// //             for (fld in form.fields) {
// //                 if($scope[fld]){
// //                     if(fld === "type"){
// //                         data[fld] = $scope[fld].type;
// //                         if($scope[fld].type==="integer" || $scope[fld].type==="float"){
// //                             data[min] = $('#answer_min').val();
// //                             data[max] = $('#answer_max').val();
// //                             labels[min]= "Min";
// //                             labels[max]= "Max";
// //                         }
// //                     }
// //                     else{
// //                         data[fld] = $scope[fld];
// //                     }
// //                     labels[fld] = form.fields[fld].label;
// //                 }
// //             }
// //             Wait('stop');
// //             $scope.survey_questions.push(data);
// //             $('#new_question .aw-form-well').remove();
// //             // for(fld in form.fields){
// //             //     $scope[fld] = '';
// //             // }
// //             $scope.finalizeQuestion(data , labels);

// //         } catch (err) {
// //             Wait('stop');
// //             Alert("Error", "Error parsing extra variables. Parser returned: " + err);
// //         }
// //     };
// //     // Save
// //     $scope.formSave = function () {
// //         generator.clearApiErrors();
// //         Wait('start');
// //         var url;
// //         if($scope.Store("survey_for_new_job_template") && $scope.Store("survey_for_new_job_template")!==false){
// //             $scope.Store('survey_for_new_job_template', {
// //                 // survey_created: true,
// //                 name: $scope.survey_name,
// //                 description: $scope.survey_description,
// //                 spec:$scope.survey_questions
// //             });
// //             Wait('stop');
// //             $location.path("/job_templates/add/");
// //         }
// //         else {
// //             url = GetBasePath(base)+ id + '/survey_spec/';

// //             Rest.setUrl(url);
// //             Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec:$scope.survey_questions })
// //                 .success(function () {
// //                     Wait('stop');
// //                     $location.path("/job_templates/"+id);
// //                 })
// //                 .error(function (data, status) {
// //                     ProcessErrors($scope, data, status, form, { hdr: 'Error!',
// //                         msg: 'Failed to add new survey. Post returned status: ' + status });
// //                 });
// //         }
// //     };

// //     // Cancel
// //     $scope.formReset = function () {
// //         $rootScope.flashMessage = null;
// //         generator.reset();
// //     };
// // }
