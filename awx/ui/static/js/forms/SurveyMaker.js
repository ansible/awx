/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  SurveyMaker.js
 *  Form definition for survey maker model
 *
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:SurveyMaker
 * @description This form is for adding/editing a survey
*/
angular.module('SurveyMakerFormDefinition', [])
    .value('SurveyMakerForm', {

        addTitle: 'Add Survey', //Title in add mode
        editTitle: 'Edit Survey', //Title in edit mode
        name: 'survey_maker', //entity or model name in singular form
        // // well: true,
        breadCrumbs: false,


        fields: {
            survey_name: {
                type: 'custom',
                control: '<div class="row">'+
                    //     '<div class="col-sm-6">
                    //         <div class="form-group">'+
                    //             '<label for="survey_name"><span class="label-text prepend-asterisk">Survey Name</span></label>
                    //                 <div>'+
                    //                     '<input type="text" ng-model="survey_name" name="survey_name" id="survey_maker_survey_name" class="form-control ng-pristine ng-invalid ng-invalid-required" required="" capitalize>'+
                    //                         '<div class="error ng-hide" id="survey_maker-survey_name-required-error" ng-show="survey_maker_form.survey_name.$dirty &amp;&amp; survey_maker_form.survey_name.$error.required">A value is required!</div>'+
                    //                         '<div class="error api-error ng-binding" id="survey_maker-survey_name-api-error" ng-bind="survey_name_api_error"></div>'+
                    // '</div></div></div>'+
                    // '<div class="col-sm-6"><div class="form-group">'+
                    // '<label for="survey_description"><span class="label-text">Survey Description</span></label><div>'+
                    // '<input type="text" ng-model="survey_description" name="survey_description" id="survey_maker_survey_description" class="form-control ng-pristine ng-valid">'+
                    // '<div class="error api-error ng-binding" id="survey_maker-survey_description-api-error" ng-bind="survey_description_api_error"></div>'+
                    // '</div></div></div>'+
                    '<div class="col-sm-12">'+
                        '<label for="survey"><span class="label-text prepend-asterisk">Questions</span></label>'+
                        '<div id="survey_maker_question_area"></div>'+
                        '<div id="finalized_questions"></div>'+
                        '<button style="display:none" type="button" class="btn btn-sm btn-primary" id="add_question_btn" ng-click="addNewQuestion()" aw-tool-tip="Create a new question" data-placement="top" data-original-title="" title="" disabled><i class="fa fa-plus fa-lg"></i>  Add Question</button>'+
                        '<div id="new_question"></div>'+
                    '</div>'+
                '</div>'//</div>'
                // label: 'Survey Name',
                // type: 'text',
                // addRequired: true,
                // editRequired: true,
                // capitalize: false,
                // // column: 1
            },

        },

        // buttons: { //for now always generates <button> tags
            // save: {
            //     ngClick: 'formSave()', //$scope.function to call on click, optional
            //     ngDisabled: true //Disable when $pristine or $invalid, optional
            // }
            // reset: {
            //     ngClick: 'formReset()',
            //     ngDisabled: true //Disabled when $pristine
            // }
        // }

    });