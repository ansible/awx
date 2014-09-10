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
        editTitle: '{{ inventory_name }}',
        name: 'question_unique',
        well: true,
        twoColumns: true,

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
            question_text: {
                realName: 'question_text',
                label: 'Question Text',
                type: 'text',
                addRequired: true,
                editRequired: true,
                capitalize: true,
                column: 1
            },
            question_description: {
                realName: 'question_description',
                label: 'Question Description',
                type: 'textarea',
                rows: 2,
                addRequired: false,
                editRequired: false,
                column: 2
            },
            response_variable_name: {
                label: 'Answer Variable Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                column: 2
                // sourceModel: 'organization',
                // sourceField: 'name',
                // ngClick: 'lookUpOrganization()',
                // awRequiredWhen: {
                //     variable: "organizationrequired",
                //     init: "true"
                // }
            },
            answer_type: {
                realName: 'answer_type',
                label: 'Answer Type',
                type: 'select',
                ngOptions: 'answer_types.name for answer_types in answer_types',
                addRequired: true,
                editRequired: true,
                column: 1

            },
            answer_options_text: {
                realName: 'answer_options',
                label: 'Answer Options',
                type: 'text',
                addRequired: true,
                editRequired: true,
                ngHide: 'answer_type.type!=="text" ',
                column: 1
            },
            answer_options_multiple_choice: {
                realName: 'answer_options',
                label: 'Multiple Choice Options',
                type: 'textarea',
                rows: 3,
                addRequired: true,
                editRequired: true,
                ngShow: 'answer_type.type==="mc" ',
                awPopOver: '<p>Type an option on each line.</p>'+
                            '<p>For example the following input:<br><br>Apple<br>\n Banana<br>\n Cherry<br><br>would be displayed as:</p>\n'+
                            '<ol><li>Apple</li><li>Banana</li><li>Cherry</li><ol>',
                dataTitle: 'Multiple Choice Options',
                dataPlacement: 'right',
                dataContainer: "body",
                column: 1
            },
            answer_options_number: {
                realName: 'answer_options',
                // label: 'Answer Options',
                type: 'custom',
                control: '<div class="row">'+
                                '<div class="col-xs-6"><label for="minimum"><span class="label-text">Minimum</span></label><input id="answer_min" type="number" class="form-control"></div>'+
                                '<div class="col-xs-6"><label for="minimum"><span class="label-text">Maximum</span></label><input id="answer_max" type="number" class="form-control"></div></div>',
                ngShow: 'answer_type.type==="number" ',
                addRequired: true,
                editRequired: true,
                column: 1
            },
            answer_options_json: {
                realName: 'answer_options',
                label: 'Answer Options',
                type: 'textarea',
                rows: 3,
                ngShow: 'answer_type.type==="json" ',
                addRequired: true,
                editRequired: true,
                awPopOver: '<p>Insert some good JSON!</p>',
                dataTitle: 'Answer Options',
                dataPlacement: 'right',
                dataContainer: "body",
                column: 1
            },
            default_answer: {
                realName: 'default_answer',
                label: 'Default Answer',
                type: 'text',
                addRequired: false,
                editRequired: false,
                column: 1
            },
            is_required: {
                label: 'Answer required or optional',
                type: 'custom',
                column: 2,
                control: '<div><label for="required"><span class="label-text">Required</span></label><input id="answer_required" type="radio" checked=true></div>'+
                                '<div><label for="optional"><span class="label-text">Optional</span></label><input id="answer_optional" type="radio"></div>',

            }
        //     answer_options: {
        //         label: 'Variables',
        //         type: 'textarea',
        //         'class': 'span12',
        //         addRequired: false,
        //         editRequird: false,
        //         rows: 6,
        //         "default": "---",
        //         awPopOver: "<p>Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
        //             "JSON:<br />\n" +
        //             "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
        //             "YAML:<br />\n" +
        //             "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
        //             '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
        //             '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
        //         dataTitle: 'Inventory Variables',
        //         dataPlacement: 'right',
        //         dataContainer: 'body'
        //     }
        // },
        },
        buttons: {
            submit_quesiton: {
                ngClick: 'submitQuestion()',
                ngDisabled: true,
                'class': 'btn btn-sm btn-primary',
                label: 'Submit Question'
            },
            reset: {
                ngClick: 'questionReset()',
                ngDisabled: true
            }
        },

        related: {

        }

    });