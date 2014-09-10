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
 * @description This controller's for the survey maker page
*/
'use strict';

function SurveyMakerAdd($scope, $rootScope, $compile, $location, $log, $routeParams, SurveyMakerForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath,
    ReturnToCaller, Wait, SurveyQuestionForm) {

    ClearScope();

    // Inject dynamic view
    var generator = GenerateForm,
        form = SurveyMakerForm,
        base = $location.path().replace(/^\//, '').split('/')[0];

    $scope.survey_questions=[];

    $scope.answer_types=[
        {name: 'Text' , type: 'text'},
        {name: 'Textarea', type: 'text'},
        {name: 'Multiple Choice (single select)', type: 'mc'},
        {name: 'Multiple Choice (multiple select)', type: 'mc'},
        {name: 'JSON', type: 'json'},
        {name: 'Integer', type: 'number'},
        {name: 'Float', type: 'number'}
    ];


    generator.inject(form, { mode: 'add', related: false, scope: $scope});
    generator.reset();

    // LoadBreadCrumbs();

    $scope.addQuestion = function(){
        GenerateForm.inject(SurveyQuestionForm, {mode:'add', id:'new_question', scope:$scope, breadCrumbs: false});
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
    $scope.finalizeQuestion= function(data){
        var html = '<div class="question_final">';
        // angular.forEach(data, function(value, key) {
        //     html+='<label for="question_text"><span class="label-text">'+data.label+'</span></label>'+data.question_text;
        // });
        html+='<label for="question_text"><span class="label-text">Question Text</span></label>'+data.question_text;
        html+='<label for="question_text"><span class="label-text">Question Question</span></label>'+data.question_description;
        html+='<label for="question_text"><span class="label-text">Answer Response Variable</span></label>'+data.response_variable_name;
        html+='<label for="question_text"><span class="label-text">Answer Type</span></label>'+data.answer_type;
        html+='<label for="question_text"><span class="label-text">Answer Options</span></label>'+data.answer_option_text;
        html+='<label for="question_text"><span class="label-text">Answer Options</span></label>'+data.answer_option_number;
        html+='<label for="question_text"><span class="label-text">Answer Options</span></label>'+data.answer_option_multiple_choice;
        html+='<label for="question_text"><span class="label-text">Default Answer</span></label>'+data.default_answer;
        html+='<label for="question_text"><span class="label-text">Answer Required</span></label>'+data.is_required;
        html+='</div>';

        $('#finalized_questions').before(html);
        $('#add_question_btn').show();
        $('#add_question_btn').removeAttr('disabled');
        $('#add_question_btn').on("click" , function(){
            $scope.addQuestion();
            $('#add_question_btn').attr('disabled', 'disabled');
        });
    };
    $scope.submitQuestion = function(){
        var form = SurveyQuestionForm,
        data = {}, labels={}, fld;
        //generator.clearApiErrors();
        Wait('start');

        try {
            for (fld in form.fields) {
                if($scope[fld]){
                    data[fld] = $scope[fld];
                   // labels[fld] = form.fields[fld].label;
                }
                // if (form.fields[fld].type === 'select' && fld !== 'playbook') {
                //     data[fld] = $scope[fld].value;
                // } else {
                //     if (fld !== 'variables') {
                //         data[fld] = $scope[fld];
                //     }
                // }
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
        var url = GetBasePath(base);
        url += (base !== 'organizations') ? $routeParams.project_id + '/organizations/' : '';
        Rest.setUrl(url);
        Rest.post({ name: $scope.name, description: $scope.description })
            .success(function (data) {
                Wait('stop');
                if (base === 'organizations') {
                    $rootScope.flashMessage = "New organization successfully created!";
                    $location.path('/organizations/' + data.id);
                } else {
                    ReturnToCaller(1);
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to add new organization. Post returned status: ' + status });
            });
    };

    // Cancel
    $scope.formReset = function () {
        $rootScope.flashMessage = null;
        generator.reset();
    };
}

SurveyMakerAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'SurveyMakerForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 'Wait', 'SurveyQuestionForm'
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