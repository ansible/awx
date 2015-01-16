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
            // variable: {
            //     label: 'Answer Variable Name',
            //     type: 'text',
            //     addRequired: true,
            //     editRequired: true,
            //     column: 1,
            //     awPopOver: '<p>The suggested format for variable names are lowercase, underscore-separated descriptive nouns.</p>'+
            //                 '<p>For example: <br>foo_bar<br>\n user_id<br>\n host_name<br>' ,
            //     dataTitle: 'Answer Variable Name',
            //     dataPlacement: 'right',
            //     dataContainer: "body"
            // },
            variable: {
                ealName: 'variable',
                type: 'custom',
                control:'<label for="variable"><span class="label-text prepend-asterisk">Answer Variable Name</span>'+
                    '<a id="awp-variable" href="" aw-pop-over="<p>The suggested format for variable names is lowercase and underscore-separated. Also note that this field cannot accept variable names with spaces.</p><p>For example: <br>foo_bar<br>'+
                    'user_id<br>host_name<br><div class=&quot;popover-footer&quot;><span class=&quot;key&quot;>esc</span> or click to close</div>" '+
                    'data-placement="right" data-container="body" data-title="Answer Variable Name" class="help-link" data-original-title="" title="" tabindex="-1"><i class="fa fa-question-circle"></i></a> </label>'+
                    '<div><input type="text" ng-model="variable" name="variable" id="survey_question_variable" class="form-control ng-pristine ng-invalid ng-invalid-required" required="" aw-survey-variable-name>'+
                    '<div class="error ng-hide" id="survey_question-variable-required-error" ng-show="survey_question_form.variable.$dirty &amp;&amp; survey_question_form.variable.$error.required">A value is required!</div>'+
                    '<div class="error ng-hide" id="survey_question-variable-variable-error" ng-show="survey_question_form.variable.$dirty &amp;&amp; survey_question_form.variable.$error.variable">The value contains an illegal character!</div>'+
                    '<div class="error ng-hide" id=survey_question-variable-duplicate-error" ng-show="duplicate">This variable is already in use.</div>' +
                    '<div class="error api-error ng-binding" id="survey_question-variable-api-error" ng-bind="variable_api_error"></div>'+
                    '</div>',
                addRequired: true,
                editRequired: true,
                column: 1
            },
            type: {
                realName: 'answer_type',
                label: 'Answer Type',
                type: 'select',
                defaultText: 'Choose an answer type',
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
            text_options: {
                realName: 'answer_options',
                type: 'custom',
                control:'<div class="row">'+
                                '<div class="col-xs-6">'+
                                    '<label for="text_min"><span class="label-text">Minimum Length</span></label><input id="text_min" type="number" name="text_min" ng-model="text_min" min=0 aw-min="0" aw-max="text_max" class="form-control" integer />'+
                                    '<div class="error" ng-show="survey_question_form.text_min.$error.number || survey_question_form.text_min.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.text_min.$error.awMax">Too high!</div>'+
                                    '<div class="error" ng-show="survey_question_form.text_min.$error.awMin">Too low!</div>'+
                                '</div>'+
                                '<div class="col-xs-6">'+
                                    '<label for="text_max"><span class="label-text">Maximum Length</span></label><input id="text_max" type="number" name="text_max" ng-model="text_max" aw-min="text_min || 0" class="form-control" integer >'+
                                    '<div class="error" ng-show="survey_question_form.text_max.$error.number || survey_question_form.text_max.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.text_max.$error.awMin">Too low!</div>'+
                                '</div>'+
                            '</div>',
                ngShow: 'type.type==="text" ',
                addRequired: true,
                editRequired: true,
                column: 2
            },
            textarea_options: {
                realName: 'answer_options',
                type: 'custom',
                control:'<div class="row">'+
                                '<div class="col-xs-6">'+
                                    '<label for="textarea_min"><span class="label-text">Minimum Length</span></label><input id="textarea_min" type="number" name="textarea_min" ng-model="textarea_min"  min=0 aw-min="0" aw-max="textarea_max" class="form-control" integer />'+
                                    '<div class="error" ng-show="survey_question_form.textarea_min.$error.number || survey_question_form.textarea_min.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.textarea_min.$error.awMax">Too high!</div>'+
                                    '<div class="error" ng-show="survey_question_form.textarea_min.$error.awMin">Too low!</div>'+
                                '</div>'+
                                '<div class="col-xs-6">'+
                                    '<label for="textarea_max"><span class="label-text">Maximum Length</span></label><input id="textarea_max" type="number" name="textarea_max" ng-model="textarea_max" aw-min="textarea_min || 0" class="form-control" integer >'+
                                    '<div class="error" ng-show="survey_question_form.textarea_max.$error.number || survey_question_form.textarea_max.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.textarea_max.$error.awMin">Too low!</div>'+
                                '</div>'+
                            '</div>',
                ngShow: 'type.type==="textarea" ',
                addRequired: true,
                editRequired: true,
                column: 2
            },
            int_options: {
                realName: 'answer_options',
                type: 'custom',
                control:'<div class="row">'+
                                '<div class="col-xs-6">'+
                                    '<label for="minimum"><span class="label-text">Minimum</span></label><input id="int_min" type="number" name="int_min" ng-model="int_min" aw-max="int_max" class="form-control" integer >'+
                                    '<div class="error" ng-show="survey_question_form.int_min.$error.number || survey_question_form.int_min.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.int_min.$error.awMax">Too high!</div>'+
                                '</div>'+
                                '<div class="col-xs-6">'+
                                    '<label for="minimum"><span class="label-text">Maximum</span></label><input id="int_max" type="number" name="int_max" ng-model="int_max" aw-min="int_min" class="form-control" integer >'+
                                    '<div class="error" ng-show="survey_question_form.int_max.$error.number || survey_question_form.int_max.$error.integer">This is not valid integer!</div>'+
                                    '<div class="error" ng-show="survey_question_form.int_max.$error.awMin">Too low!</div>'+
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
                                    '<label for="minimum"><span class="label-text">Minimum</span></label><input id="float_min" type="number" name="float_min" ng-model="float_min" class="form-control" smart-float aw-max="float_max">'+
                                    '<div class="error" ng-show="survey_question_form.float_min.$error.float">This is not valid float!</div>'+
                                    '<div class="error" ng-show="survey_question_form.float_min.$error.awMax">Too high!</div>'+
                                '</div>'+
                                '<div class="col-xs-6">'+
                                    '<label for="maximum"><span class="label-text">Maximum</span></label><input id="float_max" type="number" name="float_max" ng-model="float_max" class="form-control" smart-float  aw-min="float_min">'+
                                    '<div class="error" ng-show="survey_question_form.float_max.$error.float">This is not valid float!</div>'+
                                    '<div class="error" ng-show="survey_question_form.float_max.$error.awMin">Too low!</div>'+

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
            // default_text: {
            //     realName: 'default_answer',
            //     type: 'custom',
            //     control:  '<div>'+
            //         '<label for="default_text"><span class="label-text">Default Answer</span></label>'+
            //         '<input type="text" ng-model="default_text" name="default_text"  class="form-control" />'+
            //         '<div class="error" ng-show="survey_question_form.default_text.$error.minlength || survey_question_form.default_text.$error.maxlength"> The answer must be between {{text_min}} to {{text_max}} characters long!</div>'+
            //         '</div>',
            //     column: 2,
            //     ngShow: 'type.type === "text" '
            // },
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
                    '<input type="number" ng-model="default_int" name="default_int" aw-min="int_min" aw-max="int_max"  class="form-control" integer />'+
                    '<div class="error" ng-show="survey_question_form.default_int.$error.number || survey_question_form.default_int.$error.integer">This is not valid integer!</div>'+
                    '<div class="error" ng-show="survey_question_form.default_int.$error.awMin || survey_question_form.default_int.$error.awMax"> The value must be in range {{int_min}} to {{int_max}}!</div>'+
                    '</div>',
                column: 2,
                ngShow: 'type.type === "integer" '
            },
            default_float: {
                realName: 'default_answer',
                type: 'custom',
                control: '<div>'+
                    '<label for="default_float"><span class="label-text">Default Answer</span></label>'+
                    '<input type="number" ng-model="default_float" name="default_float" aw-min="float_min" aw-max="float_max"  class="form-control"  />'+
                    '<div class="error" ng-show="survey_question_form.default_float.$error.number || survey_question_form.default_float.$error.float">This is not valid float!</div>'+
                    '<div class="error" ng-show="survey_question_form.default_float.$error.awMin || survey_question_form.default_float.$error.awMax"> The value must be in range {{float_min}} to {{float_max}}!</div>'+
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
                ngClick: 'submitQuestion($event)',
                ngDisabled: true, //'survey_question.$valid', //"!question_name || !variable || !type || ((type.type==='multiplechoice' || type.type === 'multiselect' ) && !choices)", //|| type.type===multiselect ',//'!question_name || !variable || !type' ,
                'class': 'btn btn-sm btn-primary',
                label: 'Add Question'
            }
        }

    });