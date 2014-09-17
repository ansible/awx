/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  SurveyMaker.js
 *
 *  Controller functions for the survey maker
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:SurveyMaker
 * @description This controller's for the survey maker page.
 * The survey maker interacts with the job template page, and the two go hand in hand. The scenarios are:
 * New job template - add new survey
 * New job template - edit new survey
 * Edit existing job template - add new survey
 * Edit Existing job template - edit existing survey
 *
 * Adding a new survey to any page takes the user to the Add New Survey page
 *                   Adding a new survey to a new job template saves the survey to session memory (navigating to survey maker forces us to save JT in memory temporarily)
 *                   Adding a new survey to an existing job template send the survey to the API
 *  Editing an existing survey takes the user to the Edit Survey page
 *                  Editing a survey attached to a new job template saves the survey to session memory (saves the job template in session memory)
 *                  Editing a survey attached to an existing job template saves the survey to the API
 *
 *  The variables in local memory are cleaned out whenever the user navigates to a page (other than the Survey Maker page)
*/
'use strict';

function SurveyMakerAdd($scope, $rootScope, $compile, $location, $log, $routeParams, SurveyMakerForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath,
    ReturnToCaller, Wait, SurveyQuestionForm, Store) {

    ClearScope();

    // Inject dynamic view
    var generator = GenerateForm,
        form = SurveyMakerForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        id = $location.path().replace(/^\//, '').split('/')[1];

    $scope.survey_questions=[];
    $scope.Store = Store;
    $scope.answer_types=[
        {name: 'Text' , type: 'text'},
        {name: 'Textarea', type: 'textarea'},
        {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
        {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
        {name: 'JSON', type: 'json'},
        {name: 'Integer', type: 'integer'},
        {name: 'Float', type: 'number'}
    ];


    generator.inject(form, { mode: 'add', related: false, scope: $scope});
    generator.reset();
    // LoadBreadCrumbs();
    // LoadBreadCrumbs({
    //                 path: '/job_templates/' + id + '/survey',
    //                 title: 'jared rocks', // $scope.job_id + ' - ', //+ data.summary_fields.job_template.name,
    //                 altPath:  '/job_templates/' + id + '/survey',
    //             });

    $scope.addQuestion = function(){

        GenerateForm.inject(SurveyQuestionForm, {mode:'modal', id:'new_question', scope:$scope, breadCrumbs: false});
    };
    $scope.addQuestion();

// $('#question_shadow').mouseenter(function(){
//     $('#question_shadow').css({
//         "opacity": "1",
//         "border": "1px solid",
//         "border-color": "rgb(204,204,204)",
//         "border-radius": "4px"
//     });
//     $('#question_add_btn').show();
// });

// $('#question_shadow').mouseleave(function(){
//     $('#question_shadow').css({
//         "opacity": ".4",
//         "border": "1px dashed",
//         "border-color": "rgb(204,204,204)",
//         "border-radius": "4px"
//     });
//     $('#question_add_btn').hide();
// })


    // $('#question_shadow').on("click" , function(){
    //     // var survey_width = $('#survey_maker_question_area').width()-10,
    //     // html = "";

    //     // $('#add_question_btn').attr('disabled', 'disabled')
    //     // $('#survey_maker_question_area').append(html);
    //     addQuestion();
    //     $('#question_shadow').hide();
    //     $('#question_shadow').css({
    //         "opacity": ".4",
    //         "border": "1px dashed",
    //         "border-color": "rgb(204,204,204)",
    //         "border-radius": "4px"
    //     });
    // });
    $scope.finalizeQuestion= function(data, labels){
        var key,
        html = '<div class="question_final row">';

        for (key in data) {
            html+='<div class="col-xs-6"><label for="question_text"><span class="label-text">'+labels[key] +':  </span></label>'+data[key]+'</div>\n';
        }

        html+='</div>';

        $('#finalized_questions').before(html);
        $('#add_question_btn').show();
        $('#add_question_btn').removeAttr('disabled');
        $('#survey_maker_save_btn').removeAttr('disabled');
    };

    $('#add_question_btn').on("click" , function(){
            $scope.addQuestion();
            $('#add_question_btn').attr('disabled', 'disabled');
        });

    $scope.submitQuestion = function(){
        var form = SurveyQuestionForm,
        data = {},
        labels={},
        min= "min",
        max = "max",
        fld;
        //generator.clearApiErrors();
        Wait('start');

        try {
            for (fld in form.fields) {
                if($scope[fld]){
                    if(fld === "type"){
                        data[fld] = $scope[fld].type;
                        if($scope[fld].type==="integer" || $scope[fld].type==="float"){
                            data[min] = $('#answer_min').val();
                            data[max] = $('#answer_max').val();
                            labels[min]= "Min";
                            labels[max]= "Max";
                        }
                    }
                    else{
                        data[fld] = $scope[fld];
                    }
                    labels[fld] = form.fields[fld].label;
                }
            }
            Wait('stop');
            $scope.survey_questions.push(data);
            $('#new_question .aw-form-well').remove();
            // for(fld in form.fields){
            //     $scope[fld] = '';
            // }
            $scope.finalizeQuestion(data , labels);

        } catch (err) {
            Wait('stop');
            Alert("Error", "Error parsing extra variables. Parser returned: " + err);
        }
    };

    $scope.formSave = function () {
        generator.clearApiErrors();
        Wait('start');
        var url;
        if(!$scope.Store("survey_for_new_job_template") && $scope.Store("survey_for_new_job_template")!==false){
            $scope.Store('survey_for_new_job_template', {
                // survey_created: true,
                name: $scope.survey_name,
                description: $scope.survey_description,
                spec:$scope.survey_questions
            });
            Wait('stop');
            $location.path("/job_templates/add/");
        }
        else {
            url = GetBasePath(base)+ id + '/survey_spec/';

            Rest.setUrl(url);
            Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec:$scope.survey_questions })
                .success(function () {
                    Wait('stop');
                    $location.path("/job_templates/"+id);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new survey. Post returned status: ' + status });
                });
        }
    };

    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        Wait('start');
        if($scope.Store("saved_job_template_for_survey")){
            $scope.Store('survey_for_new_job_template', {
                // survey_created: true,
                name: $scope.survey_name,
                description: $scope.survey_description,
                spec:$scope.survey_questions
            });
            Wait('stop');
            $location.path("/job_templates/add/");
        }
        else{
            var url = GetBasePath(base)+ id + '/survey_spec/';
            Rest.setUrl(url);
            Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec:$scope.survey_questions })
                .success(function () {
                    Wait('stop');
                    $location.path("/job_templates/"+id);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new survey. Post returned status: ' + status });
                });
        }

    };

    // Cancel
    $scope.formReset = function () {
        $rootScope.flashMessage = null;
        generator.reset();
    };
}

SurveyMakerAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'SurveyMakerForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'Wait', 'SurveyQuestionForm', 'Store'
];

function SurveyMakerEdit($scope, $rootScope, $compile, $location, $log, $routeParams, SurveyMakerForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath,
    ReturnToCaller, Wait, SurveyQuestionForm, Store) {

    ClearScope();

    // Inject dynamic view
    var generator = GenerateForm,
        form = SurveyMakerForm,
        base = $location.path().replace(/^\//, '').split('/')[0],
        id = $location.path().replace(/^\//, '').split('/')[1],
        i, data;

    $scope.survey_questions=[];

    $scope.answer_types=[
        {name: 'Text' , type: 'text'},
        {name: 'Textarea', type: 'textarea'},
        {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
        {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
        {name: 'JSON', type: 'json'},
        {name: 'Integer', type: 'integer'},
        {name: 'Float', type: 'number'}
    ];

    $scope.Store = Store;

    generator.inject(form, { mode: 'edit', related: false, scope: $scope});
    generator.reset();
    // LoadBreadCrumbs();
    // LoadBreadCrumbs({
    //                 path: '/job_templates/' + id + '/survey',
    //                 title: 'jared rocks', // $scope.job_id + ' - ', //+ data.summary_fields.job_template.name,
    //                 altPath:  '/job_templates/' + id + '/survey',
    //             });

    $scope.addQuestion = function(){

        GenerateForm.inject(SurveyQuestionForm, {mode:'add', id:'new_question', scope:$scope, breadCrumbs: false});
    };
    // $scope.addQuestion();

// $('#question_shadow').mouseenter(function(){
//     $('#question_shadow').css({
//         "opacity": "1",
//         "border": "1px solid",
//         "border-color": "rgb(204,204,204)",
//         "border-radius": "4px"
//     });
//     $('#question_add_btn').show();
// });

// $('#question_shadow').mouseleave(function(){
//     $('#question_shadow').css({
//         "opacity": ".4",
//         "border": "1px dashed",
//         "border-color": "rgb(204,204,204)",
//         "border-radius": "4px"
//     });
//     $('#question_add_btn').hide();
// })


    // $('#question_shadow').on("click" , function(){
    //     // var survey_width = $('#survey_maker_question_area').width()-10,
    //     // html = "";

    //     // $('#add_question_btn').attr('disabled', 'disabled')
    //     // $('#survey_maker_question_area').append(html);
    //     addQuestion();
    //     $('#question_shadow').hide();
    //     $('#question_shadow').css({
    //         "opacity": ".4",
    //         "border": "1px dashed",
    //         "border-color": "rgb(204,204,204)",
    //         "border-radius": "4px"
    //     });
    // });
    $scope.finalizeQuestion= function(data){
        var key,
        labels={
            "type": "Type",
            "question_name": "Question Text",
            "question_description": "Question Description",
            "variable": "Answer Varaible Name",
            "choices": "Choices",
            "min": "Min",
            "max": "Max",
            "required": "Required",
            "default": "Default Answer"
        },
        html = '<div class="question_final row">';

        for (key in data) {
            html+='<div class="col-xs-6"><label for="question_text"><span class="label-text">'+labels[key] +':  </span></label>'+data[key]+'</div>\n';
        }

        html+='</div>';

        $('#finalized_questions').before(html);
        $('#add_question_btn').show();
        $('#add_question_btn').removeAttr('disabled');
        $('#survey_maker_save_btn').removeAttr('disabled');
    };

    $('#add_question_btn').on("click" , function(){
            $scope.addQuestion();
            $('#add_question_btn').attr('disabled', 'disabled');
        });

    Wait('start');

    if($scope.Store("saved_job_template_for_survey") && $scope.Store("saved_job_template_for_survey").editing_survey===true){
        data = $scope.Store("survey_for_new_job_template");
        $scope.survey_name = data.name;
        $scope.survey_description = data.description;
        $scope.survey_questions = data.spec;
        for(i=0; i<$scope.survey_questions.length; i++){
            $scope.finalizeQuestion($scope.survey_questions[i]);
        }
        Wait('stop');
    }
    else{
        Rest.setUrl(GetBasePath(base)+ id + '/survey_spec/');
        Rest.get()
            .success(function (data) {
                    var i;
                    $scope.survey_name = data.name;
                    $scope.survey_description = data.description;
                    $scope.survey_questions = data.spec;
                    for(i=0; i<$scope.survey_questions.length; i++){
                        $scope.finalizeQuestion($scope.survey_questions[i]);
                    }
                    Wait('stop');
                // LoadBreadCrumbs({ path: '/organizations/' + id, title: data.name });
                // for (fld in form.fields) {
                //     if (data[fld]) {
                //         $scope[fld] = data[fld];
                //         master[fld] = data[fld];
                //     }
                // }

                // related = data.related;
                // for (set in form.related) {
                //     if (related[set]) {
                //         relatedSets[set] = {
                //             url: related[set],
                //             iterator: form.related[set].iterator
                //         };
                //     }
                // }

                // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
                // RelatedSearchInit({ scope: $scope, form: form, relatedSets: relatedSets });
                // RelatedPaginateInit({ scope: $scope, relatedSets: relatedSets });
                // $scope.$emit('organizationLoaded');
                })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
            });
    }
    $scope.submitQuestion = function(){
        var form = SurveyQuestionForm,
        data = {},
        labels={},
        min= "min",
        max = "max",
        fld;
        //generator.clearApiErrors();
        Wait('start');

        try {
            for (fld in form.fields) {
                if($scope[fld]){
                    if(fld === "type"){
                        data[fld] = $scope[fld].type;
                        if($scope[fld].type==="integer" || $scope[fld].type==="float"){
                            data[min] = $('#answer_min').val();
                            data[max] = $('#answer_max').val();
                            labels[min]= "Min";
                            labels[max]= "Max";
                        }
                    }
                    else{
                        data[fld] = $scope[fld];
                    }
                    labels[fld] = form.fields[fld].label;
                }
            }
            Wait('stop');
            $scope.survey_questions.push(data);
            $('#new_question .aw-form-well').remove();
            // for(fld in form.fields){
            //     $scope[fld] = '';
            // }
            $scope.finalizeQuestion(data , labels);

        } catch (err) {
            Wait('stop');
            Alert("Error", "Error parsing extra variables. Parser returned: " + err);
        }
    };
    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        Wait('start');
        var url;
        if($scope.Store("survey_for_new_job_template") && $scope.Store("survey_for_new_job_template")!==false){
            $scope.Store('survey_for_new_job_template', {
                // survey_created: true,
                name: $scope.survey_name,
                description: $scope.survey_description,
                spec:$scope.survey_questions
            });
            Wait('stop');
            $location.path("/job_templates/add/");
        }
        else {
            url = GetBasePath(base)+ id + '/survey_spec/';

            Rest.setUrl(url);
            Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec:$scope.survey_questions })
                .success(function () {
                    Wait('stop');
                    $location.path("/job_templates/"+id);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new survey. Post returned status: ' + status });
                });
        }
    };

    // Cancel
    $scope.formReset = function () {
        $rootScope.flashMessage = null;
        generator.reset();
    };
}

SurveyMakerEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'SurveyMakerForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'Wait', 'SurveyQuestionForm', 'Store'
];



// function OrganizationsEdit($scope, $rootScope, $compile, $location, $log, $routeParams, OrganizationForm, GenerateForm, Rest,
//     Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, Prompt, ClearScope, GetBasePath, Wait, Stream) {

//     ClearScope();

//     // Inject dynamic view
//     var form = OrganizationForm,
//         generator = GenerateForm,
//         defaultUrl = GetBasePath('organizations'),
//         base = $location.path().replace(/^\//, '').split('/')[0],
//         master = {},
//         id = $routeParams.organization_id,
//         relatedSets = {};

//     generator.inject(form, { mode: 'edit', related: true, scope: $scope});
//     generator.reset();

//     // After the Organization is loaded, retrieve each related set
//     if ($scope.organizationLoadedRemove) {
//         $scope.organizationLoadedRemove();
//     }
//     $scope.organizationLoadedRemove = $scope.$on('organizationLoaded', function () {
//         for (var set in relatedSets) {
//             $scope.search(relatedSets[set].iterator);
//         }
//         Wait('stop');
//     });

//     // Retrieve detail record and prepopulate the form
//     Wait('start');
//     Rest.setUrl(defaultUrl + id + '/');
//     Rest.get()
//         .success(function (data) {
//             var fld, related, set;
//             LoadBreadCrumbs({ path: '/organizations/' + id, title: data.name });
//             for (fld in form.fields) {
//                 if (data[fld]) {
//                     $scope[fld] = data[fld];
//                     master[fld] = data[fld];
//                 }
//             }
//             related = data.related;
//             for (set in form.related) {
//                 if (related[set]) {
//                     relatedSets[set] = {
//                         url: related[set],
//                         iterator: form.related[set].iterator
//                     };
//                 }
//             }
//             // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
//             RelatedSearchInit({ scope: $scope, form: form, relatedSets: relatedSets });
//             RelatedPaginateInit({ scope: $scope, relatedSets: relatedSets });
//             $scope.$emit('organizationLoaded');
//         })
//         .error(function (data, status) {
//             ProcessErrors($scope, data, status, form, { hdr: 'Error!',
//                 msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
//         });


//     // Save changes to the parent
//     $scope.formSave = function () {
//         var fld, params = {};
//         generator.clearApiErrors();
//         Wait('start');
//         for (fld in form.fields) {
//             params[fld] = $scope[fld];
//         }
//         Rest.setUrl(defaultUrl + id + '/');
//         Rest.put(params)
//             .success(function () {
//                 Wait('stop');
//                 master = params;
//                 $rootScope.flashMessage = "Your changes were successfully saved!";
//             })
//             .error(function (data, status) {
//                 ProcessErrors($scope, data, status, OrganizationForm, { hdr: 'Error!',
//                     msg: 'Failed to update organization: ' + id + '. PUT status: ' + status });
//             });
//     };

//     $scope.showActivity = function () {
//         Stream({
//             scope: $scope
//         });
//     };

//     // Reset the form
//     $scope.formReset = function () {
//         $rootScope.flashMessage = null;
//         generator.reset();
//         for (var fld in master) {
//             $scope[fld] = master[fld];
//         }
//     };

//     // Related set: Add button
//     $scope.add = function (set) {
//         $rootScope.flashMessage = null;
//         $location.path('/' + base + '/' + $routeParams.organization_id + '/' + set);
//     };

//     // Related set: Edit button
//     $scope.edit = function (set, id) {
//         $rootScope.flashMessage = null;
//         $location.path('/' + set + '/' + id);
//     };

//     // Related set: Delete button
//     $scope['delete'] = function (set, itm_id, name, title) {
//         $rootScope.flashMessage = null;

//         var action = function () {
//             Wait('start');
//             var url = defaultUrl + $routeParams.organization_id + '/' + set + '/';
//             Rest.setUrl(url);
//             Rest.post({ id: itm_id, disassociate: 1 })
//                 .success(function () {
//                     $('#prompt-modal').modal('hide');
//                     $scope.search(form.related[set].iterator);
//                 })
//                 .error(function (data, status) {
//                     $('#prompt-modal').modal('hide');
//                     ProcessErrors($scope, data, status, null, { hdr: 'Error!',
//                         msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
//                 });
//         };

//         Prompt({
//             hdr: 'Delete',
//             body: 'Are you sure you want to remove ' + name + ' from ' + $scope.name + ' ' + title + '?',
//             action: action
//         });

//     };
// }

// OrganizationsEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'OrganizationForm', 'GenerateForm',
//     'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit', 'Prompt', 'ClearScope', 'GetBasePath',
//     'Wait', 'Stream'
// ];