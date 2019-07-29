/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Questions
 * @description This form is for adding a question
*/

export default ['i18n', function(i18n){
    return {

        addTitle: i18n._('ADD SURVEY PROMPT'),
        editTitle: i18n._('EDIT SURVEY PROMPT'),
        titleClass: 'Form-secondaryTitle',
        base: 'survey_question',
        name: 'survey_question',
        well: true,
        cancelButton: false,

    fields: {
        question_name: {
            realName: 'question_text',
            label: i18n._('Prompt'),
            type: 'text',
            required: true,
            column: 1,
            awSurveyQuestion: true,
            class: 'Form-formGroup--singleColumn'
        },
        question_description: {
            realName: 'question_description',
            label: i18n._('Description'),
            type: 'text',
            column: 1,
            class: 'Form-formGroup--singleColumn'
        },
        variable: {
            realName: 'variable',
            type: 'custom',
            label: i18n._('Answer Variable Name'),
            control:
                '<div><input type="text" ng-model="variable" name="variable" id="survey_question_variable" class="form-control Form-textInput ng-pristine ng-invalid ng-invalid-required" required="" aw-survey-variable-name>'+
                '<div class="error ng-hide" id="survey_question-variable-required-error" ng-show="survey_question_form.variable.$dirty && survey_question_form.variable.$error.required">' + i18n._('Please enter an answer variable name.') + '</div>'+
                '<div class="error ng-hide" id="survey_question-variable-variable-error" ng-show="survey_question_form.variable.$dirty && survey_question_form.variable.$error.variable">' + i18n._('Please remove the illegal character from the survey question variable name.') + '</div>'+
                '<div class="error ng-hide" id="survey_question-variable-duplicate-error" ng-show="duplicate">' + i18n._('This question variable is already in use.  Please enter a different variable name.') + '</div>' +
                '<div class="error api-error ng-binding" id="survey_question-variable-api-error" ng-bind="variable_api_error"></div>'+
                '</div>',
            awPopOver: i18n._("The suggested format for variable names is lowercase and underscore-separated (for example, foo_bar, user_id, host_name, etc.). Variable names with spaces are not allowed."),
            dataTitle: i18n._('Answer Variable Name'),
            dataPlacement: 'right',
            dataContainer: "body",
            required: true,
            column: 1,
            class: 'Form-formGroup--singleColumn'
        },
        type: {
            realName: 'answer_type',
            label: i18n._('Answer Type'),
            type: 'select',
            defaultText: i18n._('Choose an answer type'),
            ngOptions: 'answer_types.name for answer_types in answer_types track by answer_types.type',
            required: true,
            awPopOver: i18n._('Choose an answer type or format you want as the prompt for the user. Refer to the Ansible Tower Documentation for more additional information about each option.'),
            dataTitle: i18n._('Answer Type'),
            dataPlacement: 'right',
            dataContainer: "body",
            column: 2,
            ngChange: 'typeChange()',
            class: 'Form-formGroup--singleColumn'
        },
        choices: {
            realName: 'answer_options',
            label: i18n._('Multiple Choice Options'),
            type: 'textarea',
            rows: 3,
            required: true,

            ngRequired: "type.type=== 'multiselect' || type.type=== 'multiplechoice' " ,
            ngShow: 'type.type=== "multiselect" || type.type=== "multiplechoice" ',
            column: 2,
            class: 'Form-formGroup--singleColumn'
        },
        text_options: {
            realName: 'answer_options',
            type: 'custom',
            control:'<div class="row">'+
                            '<div class="col-sm-6">'+
                                '<label for="text_min"><span class="Form-inputLabel">' + i18n._('Minimum Length') + '</span></label><input id="text_min" name="text_min" ng-model="text_min" min=0 aw-min="0" aw-max="text_max" aw-spinner="text_min" integer>'+
                                '<div class="error" ng-show="survey_question_form.text_min.$error.integer || survey_question_form.text_min.$error.number">' + i18n._('The minimum length you entered is not a valid number.  Please enter a whole number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.text_min.$error.awMax">' + i18n._('The minimium length is too high.  Please enter a lower number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.text_min.$error.awMin">' + i18n._('The minimum length is too low.  Please enter a positive number.') + '</div>'+
                            '</div>'+
                            '<div class="col-sm-6">'+
                                '<label for="text_max"><span class="Form-inputLabel">' + i18n._('Maximum Length') + '</span></label><input id="text_max" name="text_max" ng-model="text_max" aw-min="text_min || 0" min=0 aw-spinner="text_max" integer>'+
                                '<div class="error" ng-show="survey_question_form.text_max.$error.integer || survey_question_form.text_max.$error.number">' + i18n._('The maximum length you entered is not a valid number.  Please enter a whole number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.text_max.$error.awMin">' + i18n._('The maximum length is too low.  Please enter a number larger than the minimum length you set.') + '</div>'+
                            '</div>'+
                        '</div>',
            ngShow: 'type.type==="text" ',
            required: true,
            column: 2,
            class: 'Form-formGroup--singleColumn'
        },
        textarea_options: {
            realName: 'answer_options',
            type: 'custom',
            control:'<div class="row">'+
                            '<div class="col-sm-6">'+
                                '<label for="textarea_min"><span class="Form-inputLabel">' + i18n._('Minimum Length') + '</span></label><input id="textarea_min" type="number" name="textarea_min" ng-model="textarea_min"  min=0 aw-min="0" aw-max="textarea_max" class="form-control Form-textInput" integer />'+
                                '<div class="error" ng-show="survey_question_form.textarea_min.$error.integer || survey_question_form.textarea_min.$error.number">' + i18n._('The minimum length you entered is not a valid number.  Please enter a whole number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.textarea_min.$error.awMax">' + i18n._('The minimium length is too high.  Please enter a lower number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.textarea_min.$error.awMin">' + i18n._('The minimum length is too low.  Please enter a positive number.') + '</div>'+
                            '</div>'+
                            '<div class="col-sm-6">'+
                                '<label for="textarea_max"><span class="Form-inputLabel">' + i18n._('Maximum Length') + '</span></label><input id="textarea_max" type="number" name="textarea_max" ng-model="textarea_max" aw-min="textarea_min || 0" min=0 class="form-control Form-textInput" integer >'+
                                '<div class="error" ng-show="survey_question_form.textarea_max.$error.integer || survey_question_form.textarea_max.$error.number">' + i18n._('The maximum length you entered is not a valid number.  Please enter a whole number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.textarea_max.$error.awMin">' + i18n._('The maximum length is too low.  Please enter a number larger than the minimum length you set.') + '</div>'+
                            '</div>'+
                        '</div>',
            ngShow: 'type.type==="textarea" ',
            required: true,
            column: 2,
            class: 'Form-formGroup--singleColumn'
        },
        password_options: {
            realName: 'answer_options',
            type: 'custom',
            control:'<div class="row">'+
                            '<div class="col-sm-6">'+
                                '<label for="password_min"><span class="Form-inputLabel">' + i18n._('Minimum Length') + '</span></label><input id="password_min" type="number" name="password_min" ng-model="password_min" min=0 aw-min="0" aw-max="password_max" class="form-control Form-textInput" integer />'+
                                '<div class="error" ng-show="survey_question_form.password_min.$error.integer || survey_question_form.password_min.$error.number">' + i18n._('The minimum length you entered is not a valid number.  Please enter a whole number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.password_min.$error.awMax">' + i18n._('The minimium length is too high.  Please enter a lower number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.password_min.$error.awMin">' + i18n._('The minimum length is too low.  Please enter a positive number.') + '</div>'+
                            '</div>'+
                            '<div class="col-sm-6">'+
                                '<label for="password_max"><span class="Form-inputLabel">' + i18n._('Maximum Length') + '</span></label><input id="password_max" type="number" name="password_max" ng-model="password_max" aw-min="password_min || 0" min=0 class="form-control Form-textInput" integer >'+
                                '<div class="error" ng-show="survey_question_form.password_max.$error.integer || survey_question_form.password_max.$error.number">' + i18n._('The maximum length you entered is not a valid number.  Please enter a whole number.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.password_max.$error.awMin">' + i18n._('The maximum length is too low.  Please enter a number larger than the minimum length you set.') + '</div>'+
                            '</div>'+
                        '</div>',
            ngShow: 'type.type==="password" ',
            required: true,

            column: 2,
            class: 'Form-formGroup--singleColumn'
        },
        int_options: {
            realName: 'answer_options',
            type: 'custom',
            control:'<div class="row">'+
                            '<div class="col-sm-6">'+
                                '<label for="minimum"><span class="Form-inputLabel">' + i18n._('Minimum') + '</span></label><input id="int_min" type="number" name="int_min" ng-model="int_min" aw-max="int_max" class="form-control Form-textInput" integer >'+
                                '<div class="error" ng-show="survey_question_form.int_min.$error.integer || survey_question_form.int_min.$error.number">' + i18n._('Please enter a valid integer.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.int_min.$error.awMax">' + i18n._('Please enter a smaller integer.') + '</div>'+
                            '</div>'+
                            '<div class="col-sm-6">'+
                                '<label for="minimum"><span class="Form-inputLabel">' + i18n._('Maximum') + '</span></label><input id="int_max" type="number" name="int_max" ng-model="int_max" aw-min="int_min" class="form-control Form-textInput" integer >'+
                                '<div class="error" ng-show="survey_question_form.int_max.$error.integer || survey_question_form.int_max.$error.number">' + i18n._('Please enter a valid integer.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.int_max.$error.awMin">' + i18n._('Please enter a larger integer.') + '</div>'+
                            '</div>'+
                        '</div>',
            ngShow: 'type.type==="integer" ',
            required: true,
            column: 2,
            class: 'Form-formGroup--singleColumn'
        },
        float_options: {
            realName: 'answer_options',
            type: 'custom',
            control: '<div class="row">'+
                            '<div class="col-sm-6">'+
                                '<label for="minimum"><span class="Form-inputLabel">' + i18n._('Minimum') + '</span></label><input id="float_min" type="number" name="float_min" ng-model="float_min" class="form-control Form-textInput" smart-float aw-max="float_max">'+
                                '<div class="error" ng-show="survey_question_form.float_min.$error.float || survey_question_form.float_min.$error.number">' + i18n._('Please enter a valid float.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.float_min.$error.awMax">' + i18n._('Please enter a smaller float.') + '</div>'+
                            '</div>'+
                            '<div class="col-sm-6">'+
                                '<label for="maximum"><span class="Form-inputLabel">' + i18n._('Maximum<') + '/span></label><input id="float_max" type="number" name="float_max" ng-model="float_max" class="form-control Form-textInput" smart-float  aw-min="float_min">'+
                                '<div class="error" ng-show="survey_question_form.float_max.$error.float">' + i18n._('Please enter a valid float.') + '</div>'+
                                '<div class="error" ng-show="survey_question_form.float_max.$error.awMin">' + i18n._('Please enter a larger float.') + '</div>'+

                            '</div>'+
                        '</div>',
            ngShow: 'type.type==="float" ',
            required: true,
            column: 2,
            class: 'Form-formGroup--singleColumn'
        },
        default:{
            realName: 'default_answer',
            type: 'custom' ,
            control: '<div class="form-group" >'+
                '<label for="default"><span class="Form-inputLabel">' + i18n._('Default Answer') + '</span></label>'+
                '<div>'+
                '<input type="text" ng-model="default" name="default" id="default" class="form-control Form-textInput">'+
                '<div class="error ng-hide" id="survey_question-default-duplicate-error" ng-show="invalidChoice">' + i18n._('Please enter an answer from the choices listed.') + '</div>' +
                '<div class="error ng-hide" id="survey_question-default-duplicate-error" ng-show="minTextError">' + i18n._('The answer is shorter than the minimium length. Please make the answer longer.') + '</div>' +
                '<div class="error ng-hide" id="survey_question-default-duplicate-error" ng-show="maxTextError">' + i18n._('The answer is longer than the maximum length. Please make the answer shorter.') + '</div>' +
                '<div class="error api-error ng-binding" id="survey_question-default-api-error" ng-bind="default_api_error"></div>'+
                '</div>'+
                '</div>',
            column: 2,
            ngShow: 'type.type === "text" || type.type === "multiplechoice" ',
            class: 'Form-formGroup--singleColumn'
        },
        default_multiselect: {
            realName: 'default_answer' ,
            type: 'custom',
            control: '<div class="form-group">'+
                '<label for="default_multiselect"><span class="Form-inputLabel">' + i18n._('Default Answer') + '</span></label>'+
                '<div>'+
                '<textarea rows="3" ng-model="default_multiselect" name="default_multiselect" class="form-control Form-textArea ng-pristine ng-valid" id="default_multiselect" aw-watch=""></textarea>'+
                '<div class="error ng-hide" id="survey_question-default_multiselect-duplicate-error" ng-show="invalidChoice">' + i18n._('Please enter an answer/answers from the choices listed.') + '</div>' +
                '<div class="error api-error ng-binding" id="survey_question-default_multiselect-api-error" ng-bind="default_multiselect_api_error"></div>'+
                '</div>'+
                '</div>',
            column: 2,
            ngShow: 'type.type==="multiselect" ',
            class: 'Form-formGroup--singleColumn'
        },
        default_int: {
            realName: 'default_answer',
            type: 'custom',
            control:  '<div>'+
                '<label for="default_int"><span class="Form-inputLabel">' + i18n._('Default Answer') + '</span></label>'+
                '<input type="number" ng-model="default_int" name="default_int" aw-range range-min="int_min" range-max="int_max" class="form-control Form-textInput" integer />'+
                '<div class="error" ng-show="survey_question_form.default_int.$error.number || survey_question_form.default_int.$error.integer">' + i18n._('Please enter a valid integer.') + '</div>'+
                '<div class="error" ng-show="survey_question_form.default_int.$error.awRangeMin">' + i18n._('Please enter a minimum default of {{int_min}}.') + '</div>'+
                '<div class="error" ng-show="survey_question_form.default_int.$error.awRangeMax">' + i18n._('Please enter a maximum default of {{int_max}}.') + '</div>'+
                '</div>',
            column: 2,
            ngShow: 'type.type === "integer" ',
            class: 'Form-formGroup--singleColumn'
        },
        default_float: {
            realName: 'default_answer',
            type: 'custom',
            control: '<div>'+
                '<label for="default_float"><span class="Form-inputLabel">' + i18n._('Default Answer') + '</span></label>'+
                '<input type="number" ng-model="default_float" name="default_float" aw-range range-min="float_min" range-max="float_max" class="form-control Form-textInput"  />'+
                '<div class="error" ng-show="survey_question_form.default_float.$error.number || survey_question_form.default_float.$error.float">' + i18n._('Please enter a valid float.') + '</div>'+
                '<div class="error" ng-show="survey_question_form.default_float.$error.awRangeMin">' + i18n._('Please enter a minimum default of {{float_min}}.') + '</div>'+
                '<div class="error" ng-show="survey_question_form.default_float.$error.awRangeMax">' + i18n._('Please enter a maximum default of {{float_max}}.') + '</div>'+
                '</div>',
            column: 2,
            ngShow: 'type.type=== "float" ',
            class: 'Form-formGroup--singleColumn'
        },
        default_textarea: {
            realName: "default_answer" ,
            type: 'custom',
            control: '<div class="form-group Form-formGroup Form-formGroup--singleColumn">'+
                '<label for="default_textarea"><span class="Form-inputLabel">' + i18n._('Default Answer') + '</span></label>'+
                '<div>'+
                '<textarea rows="3" ng-model="default_textarea" name="default_textarea" class="form-control Form-textArea ng-valid ng-dirty" id="default_textarea"></textarea>'+
                '<div class="error ng-hide" id="survey_question-default-duplicate-error" ng-show="minTextError">' + i18n._('The answer is shorter than the minimium length. Please make the answer longer.') + '</div>' +
                '<div class="error ng-hide" id="survey_question-default-duplicate-error" ng-show="maxTextError">' + i18n._('The answer is longer than the maximum length. Please make the answer shorter.') + '</div>' +
                '<div class="error api-error ng-binding" id="survey_question-default_textarea-api-error" ng-bind="default_textarea_api_error"></div>'+
                '</div>'+
                '</div>',
            column : 2,
            ngShow: 'type.type === "textarea" ',
            class: 'Form-formGroup--singleColumn'
        },
        default_password: {
            realName: 'default_answer' ,
            type: 'custom' ,
            control: '<div class="form-group">'+
                '<label for="default_password"><span class="Form-inputLabel">' + i18n._('Default Answer') + '</span></label>'+
                '<div>'+
                '<div class="input-group">'+
                '<span class="input-group-btn input-group-prepend">'+
                '<button type="button" class="btn btn-default show_input_button" id="default_password_show_input_button" aw-tool-tip="Toggle the display of plaintext." aw-tip-placement="top" ng-click="toggleInput(&quot;#default_password&quot;)" data-container="#survey-modal-dialog" data-original-title="" title="">SHOW</button>'+
                '</span>'+
                '<input id="default_password" type="password" ng-model="default_password" name="default_password" class="form-control Form-textInput" autocomplete="false">'+
                '</div>'+
                '<div class="error ng-hide" id="survey_question-default-duplicate-error" ng-show="minTextError">' + i18n._('The answer is shorter than the minimium length. Please make the answer longer.') + '</div>' +
                '<div class="error ng-hide" id="survey_question-default-password-duplicate-error" ng-show="maxTextError">' + i18n._('The answer is longer than the maximum length. Please make the answer shorter.') + '</div>' +
                '<div class="error api-error ng-binding" id="survey_question-default-password-api-error" ng-bind="default_api_error"></div>'+
                '</div>'+
                '</div>',
            column: 2,
            ngShow: 'type.type === "password" ',
            class: 'Form-formGroup--singleColumn'
        },
        required: {
            realName: 'required_answer',
            label: i18n._('Required'),
            type: 'checkbox',
            column: 2,
            class: 'Form-formGroup--singleColumn'
        }
    },
    buttons: {
        question_cancel : {
            label: i18n._('Clear'),
            'class' : 'btn btn-default Form-cancelButton',
            ngClick: 'generateAddQuestionForm()',
            ngDisabled: 'survey_question_form.$pristine'
        },
        submit_question: {
            ngClick: 'submitQuestion($event)',
            ngDisabled: true,
            'class': 'btn btn-sm Form-saveButton',
            label: '{{editQuestionIndex === null ? "+ ADD" : "UPDATE"}}'
        }
    }
};
}];
