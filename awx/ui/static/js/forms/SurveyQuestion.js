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
        // editTitle: '{{ survey_name }}',
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
            question_name: {
                realName: 'question_text',
                label: 'Text',
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
                // sourceModel: 'organization',
                // sourceField: 'name',
                // ngClick: 'lookUpOrganization()',
                // awRequiredWhen: {
                //     variable: "organizationrequired",
                //     init: "true"
                // }
            },
            type: {
                realName: 'answer_type',
                label: 'Answer Type',
                type: 'select',
                ngOptions: 'answer_types.name for answer_types in answer_types track by answer_types.type',
                addRequired: true,
                editRequired: true,
                column: 2

            },
            // answer_options_text: {
            //     realName: 'answer_options',
            //     label: 'Answer Options',
            //     type: 'text',
            //     addRequired: true,
            //     editRequired: true,
            //     ngHide: 'answer_type.type!=="text" ',
            //     column: 1
            // },
            choices: {
                realName: 'answer_options',
                label: 'Multiple Choice Options',
                type: 'textarea',
                rows: 3,
                addRequired: true,
                editRequired: true,
                ngShow: 'type.type==="multiselect" || type.type==="multiplechoice" ',
                awPopOver: '<p>Type an option on each line.</p>'+
                            '<p>For example the following input:<br><br>Apple<br>\n Banana<br>\n Cherry<br><br>would be displayed as:</p>\n'+
                            '<ol><li>Apple</li><li>Banana</li><li>Cherry</li><ol>',
                dataTitle: 'Multiple Choice Options',
                dataPlacement: 'right',
                dataContainer: "body",
                column: 2
            },
            answer_options_number: {
                realName: 'answer_options',
                // label: 'Answer Options',
                type: 'custom',
                control: '<div class="row">'+
                                '<div class="col-xs-6"><label for="minimum"><span class="label-text">Minimum</span></label><input id="answer_min" type="number" class="form-control"></div>'+
                                '<div class="col-xs-6"><label for="minimum"><span class="label-text">Maximum</span></label><input id="answer_max" type="number" class="form-control"></div></div>',
                ngShow: 'type.type==="integer" || type.type==="float" ',
                addRequired: true,
                editRequired: true,
                column: 2
            },
            // answer_options_json: {
            //     realName: 'answer_options',
            //     label: 'Answer Options',
            //     type: 'textarea',
            //     rows: 3,
            //     ngShow: 'type.type==="json" ',
            //     addRequired: true,
            //     editRequired: true,
            //     awPopOver: '<p>Insert some good JSON!</p>',
            //     dataTitle: 'Answer Options',
            //     dataPlacement: 'right',
            //     dataContainer: "body",
            //     column: 1
            // },
            default: {
                realName: 'default_answer',
                label: 'Default Answer',
                type: 'text',
                addRequired: false,
                editRequired: false,
                column: 2
            },
            required: {
                realName: 'required_answer',
                label: 'Required',
                type: 'checkbox',
                // checked: true,
                addRequired: false,
                editRequired: false,
                column: 2
                // trueValue: true
                // label: 'Answer required or optional',
                // type: 'custom',
                // column: 2,
                // control: '<div><label for="required"><span class="label-text">Required</span></label><input id="answer_required" type="radio" checked=true></div>'+
                //                 '<div><label for="optional"><span class="label-text">Optional</span></label><input id="answer_optional" type="radio"></div>',

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
                label: 'Add Question'
            }
        },

        related: {

        }

    });