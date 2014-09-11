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
        well: true,
        //breadCrumbs:true,
        // collapse: true,
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
                label: 'Survey Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: false
            },
            survey_description: {
                label: 'Survey Description',
                type: 'text',
                addRequired: false,
                editRequired: false
            },
            questions: {
                type: 'custom',
                control: '<label for="survey"><span class="label-text prepend-asterisk">Questions</span></label>'+
                    '<div id="survey_maker_question_area"></div><div id="finalized_questions"></div>'+
                    '<button style="display:none" type="button" class="btn btn-sm btn-primary" id="add_question_btn" aw-tool-tip="Create a new question" data-placement="top" data-original-title="" title="" disabled><i class="fa fa-plus fa-lg"></i>  Add Question</button>'+
                    '<div id="new_question"></div>'

            }
        },

        buttons: { //for now always generates <button> tags
            save: {
                ngClick: 'formSave()', //$scope.function to call on click, optional
                ngDisabled: true //Disable when $pristine or $invalid, optional
            },
            reset: {
                ngClick: 'formReset()',
                ngDisabled: true //Disabled when $pristine
            }
        }

    });