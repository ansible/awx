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
angular.module('SurveyTakerFormDefinition', [])
    .value('SurveyTakerForm', {

        // addTitle: 'Add Survey', //Title in add mode
        // editTitle: 'Edit Survey', //Title in edit mode
        name: 'survey_taker', //entity or model name in singular form
        // // well: true,
        breadCrumbs: false,
        // twoColumns: true,
        // // collapse: true,
        // collapseTitle: "Properties",
        // collapseMode: 'edit',
        // collapseOpen: true,

        // actions: {
        //     stream: {
        //         'class': "btn-primary btn-xs activity-btn",
        //         ngClick: "showActivity()",
        //         awToolTip: "View Activity Stream",
        //         dataPlacement: "top",
        //         icon: "icon-comments-alt",
        //         mode: 'edit',
        //         iconSize: 'large'
        //     }
        // },

        fields: {
            survey_name: {
                type: 'custom',
                control: '<div class="row">'+
                    '<div class="col-sm-12">'+//<label for="survey"><span class="label-text prepend-asterisk">Questions</span></label>'+
                    '<div id="survey_taker_description"></div>' +
                    '<div id="survey_maker_question_area"></div><div id="survey_taker_finalized_questions"></div>'+
                    //'<button style="display:none" type="button" class="btn btn-sm btn-primary" id="add_question_btn" ng-click="addNewQuestion()" aw-tool-tip="Create a new question" data-placement="top" data-original-title="" title="" disabled><i class="fa fa-plus fa-lg"></i>  Add Question</button>'+
                    '<div id="new_question"></div></div></div>'

            },

        },

        buttons: { //for now always generates <button> tags
            // save: {
            //     ngClick: 'formSave()', //$scope.function to call on click, optional
            //     ngDisabled: true //Disable when $pristine or $invalid, optional
            // }
            // reset: {
            //     ngClick: 'formReset()',
            //     ngDisabled: true //Disabled when $pristine
            // }
        }

    });