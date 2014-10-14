/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Inventories.js
 *  Form definition for question model
 *
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:Questions
 * @description This form is for adding a question
*/
angular.module('SurveyQuestionFormDefinition', [])
    .value('SurveyQuestionForm', {

        addTitle: 'Add Question',
        editTitle: 'Edit Question',
        base: 'survey_question',
        name: 'survey_question',
        well: true,
        twoColumns: true,
        breadcrumbs: false,

        fields: {
            question_name: {
                realName: 'question_text',
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                column: 1,
                awSurveyQuestion: true
            },
            question_description: {
                realName: 'question_description',
                label: 'Description',
                type: 'text',
                // rows: 2,
                addRequired: false,
                editRequired: false,
                column: 1
            },
            variable: {
                label: 'Answer Variable Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                column: 1
            },
            type: {
                realName: 'answer_type',
                label: 'Answer Type',
                type: 'select',
                ngOptions: 'answer_types.name for answer_types in answer_types track by answer_types.type',
                addRequired: true,
                editRequired: true,
                column: 2,
                ngChange: 'typeChange()'
            },
            choices: {
                realName: 'answer_options',
                label: 'Multiple Choice Options',
                type: 'textarea',
                rows: 3,
                addRequired: true,
                editRequired: true,
                ngRequired: "type.type=== 'multiselect' || type.type=== 'multiplechoice' " ,
                ngShow: 'type.type=== "multiselect" || type.type=== "multiplechoice" ',
                awPopOver: '<p>Type an option on each line.</p>'+
                            '<p>For example the following input:<br><br>Apple<br>\n Banana<br>\n Cherry<br><br>would be displayed as:</p>\n'+
                            '<ol><li>Apple</li><li>Banana</li><li>Cherry</li></ol>',
                dataTitle: 'Multiple Choice Options',
                dataPlacement: 'right',
                dataContainer: "body",
                column: 2
            },
            int_options: {
                realName: 'answer_options',
                type: 'custom',
                control:'<div class="row">'+
                                '<div class="col-xs-6">'+
                                    '<label for="minimum"><span class="label-text">Minimum</span></label><input id="int_min" type="number" name="int_min" ng-model="int_min" ng-max="int_max" class="form-control" integer >'+
                                    '<div class="error" ng-show="survey_question_form.int_min.$error.number || survey_question_form.int_min.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.int_min.$error.ngMax">Too high!</div>'+
                                '</div>'+
                                '<div class="col-xs-6">'+
                                    '<label for="minimum"><span class="label-text">Maximum</span></label><input id="int_max" type="number" name="int_max" ng-model="int_max" ng-min="int_min" class="form-control" integer >'+
                                    '<div class="error" ng-show="survey_question_form.int_max.$error.number || survey_question_form.int_max.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.int_max.$error.ngMin">Too low!</div>'+
                                '</div>'+
                            '</div>',
                ngShow: 'type.type==="integer" ',
                addRequired: true,
                editRequired: true,
                column: 2
            },
            float_options: {
                realName: 'answer_options',
                type: 'custom',
                control: '<div class="row">'+
                                '<div class="col-xs-6">'+
                                    '<label for="minimum"><span class="label-text">Minimum</span></label><input id="float_min" type="number" name="float_min" ng-model="float_min" class="form-control" smartFloat >'+
                                    '<div class="error" ng-show="survey_question_form.float_min.$invalid">This is not valid float!</div>'+
                                '</div>'+
                                '<div class="col-xs-6">'+
                                    '<label for="minimum"><span class="label-text">Maximum</span></label><input id="float_max" type="number" name="float_max" ng-model="float_max" class="form-control" smartFloat >'+
                                    '<div class="error" ng-show="survey_question_form.float_max.$invalid">This is not valid float!</div>'+
                                '</div>'+
                            '</div>',
                ngShow: 'type.type==="float" ',
                addRequired: true,
                editRequired: true,
                column: 2
            },
            default: {
                realName: 'default_answer',
                label: 'Default Answer',
                type: 'text',
                addRequired: false,
                editRequired: false,
                column: 2,
                ngHide: 'type.type === "textarea" || type.type === "multiselect" || type.type === "integer" || type.type === "float" '
            },
            default_multiselect: {
                realName: 'default_answer',
                label: 'Default Answer',
                type: 'textarea',
                rows: 3,
                addRequired: false,
                editRequired: false,
                column: 2,
                ngShow: 'type.type === "multiselect" '
            },
            default_int: {
                realName: 'default_answer',
                type: 'custom',
                control:  '<div>'+
                    '<label for="default_int"><span class="label-text">Default Answer</span></label>'+
                    '<input type="number" ng-model="default_int" name="default_int" ng-min="int_min" ng-max="int_max"  class="form-control" integer />'+
                    '<div class="error" ng-show="survey_question_form.default_int.$error.number || survey_question_form.default_int.$error.integer">This is not valid integer!</div>'+
                    '<div class="error" ng-show="survey_question_form.default_int.$error.ngMin || survey_question_form.default_int.$error.ngMax"> The value must be in range {{int_min}} to {{int_max}}!</div>'+
                    '</div>',
                column: 2,
                ngShow: 'type.type === "integer" '
            },
            default_float: {
                realName: 'default_answer',
                type: 'custom',
                control: '<div>'+
                    '<label for="default_float"><span class="label-text">Default Answer</span></label>'+
                    '<input type="number" ng-model="default_float" name="default_float" ng-min="float_min" ng-max="float_max"  class="form-control" integer />'+
                    '<div class="error" ng-show="survey_question_form.default_float.$error.number || survey_question_form.default_float.$error.float">This is not valid float!</div>'+
                    '<div class="error" ng-show="survey_question_form.default_float.$error.ngMin || survey_question_form.default_float.$error.ngMax"> The value must be in range {{float_min}} to {{float_max}}!</div>'+
                    '</div>',
                column: 2,
                ngShow: 'type.type=== "float" '
            },
            default_textarea: {
                realName: 'default_answer',
                label: 'Default Answer',
                type: 'textarea',
                rows: 3,
                addRequired: false,
                editRequired: false,
                column: 2,
                ngShow: 'type.type === "textarea" '
            },
            required: {
                realName: 'required_answer',
                label: 'Required',
                type: 'checkbox',
                addRequired: false,
                editRequired: false,
                column: 2
            }
        },
        buttons: {
            question_cancel : {
                label: 'Cancel',
                'class' : 'btn btn-default',
                ngClick: 'cancelQuestion($event)'
            },
            submit_question: {
                ngClick: 'submitQuestion()',
                ngDisabled: true, //'survey_question.$valid', //"!question_name || !variable || !type || ((type.type==='multiplechoice' || type.type === 'multiselect' ) && !choices)", //|| type.type===multiselect ',//'!question_name || !variable || !type' ,
                'class': 'btn btn-sm btn-primary',
                label: 'Add Question'
            }
        }

    });