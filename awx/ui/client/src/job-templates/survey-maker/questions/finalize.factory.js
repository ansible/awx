/**
 * Takes a finalized question and displays it on the survey maker page
 *
 * FinalizeQuestion({
 *     scope:       $scope containing list of survey form fields
 *     question: question object that was submitted by the question form
 *     id:          id of job template that survey is attached to
 *     callback:    $scope.$emit label to call when delete is completed
 * })
 *
 */

export default
    function FinalizeQuestion(GetBasePath, Rest, Wait, ProcessErrors, $compile, Empty, $filter, questionScope) {
        return function(params) {

            var question = params.question,
                scope = questionScope(question, params.scope),
                index = params.index,
                required,
                element,
                max,
                min,
                defaultValue,
                html = "";

            question.index = index;
            question.question_name = $filter('sanitize')(question.question_name);
            question.question_description = (question.question_description) ? $filter('sanitize')(question.question_description) : undefined;


            if(!$('#question_'+question.index+':eq(0)').is('div')){
                html+='<div id="question_'+question.index+'" class="question_final row"></div>';
                $('#finalized_questions').append(html);
            }

            required = (question.required===true) ? "prepend-asterisk" : "";
            html = '<div class="question_title col-xs-12">';
            html += '<label for="'+question.variable+'"><span class="label-text '+required+'"> '+question.question_name+'</span></label>';
            html += '</div>';

            if(!Empty(question.question_description)){
                html += '<div class="col-xs-12 description"><i>'+question.question_description+'</i></div>\n';
            }

            if(question.type === 'text' ){
                defaultValue = (question.default) ? question.default : "";
                defaultValue = $filter('sanitize')(defaultValue);
                defaultValue = scope.serialize(defaultValue);
                html+='<div class="row">'+
                    '<div class="col-xs-8">'+
                    '<input type="text" placeholder="'+defaultValue+'"  class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" readonly>'+
                    '</div></div>';
            }
            if(question.type === "textarea"){
                defaultValue = (question.default) ? question.default : (question.default_textarea) ? question.default_textarea:  "" ;
                defaultValue =  $filter('sanitize')(defaultValue);
                defaultValue = scope.serialize(defaultValue);
                html+='<div class="row">'+
                    '<div class="col-xs-8 input_area">'+
                    '<textarea class="form-control ng-pristine ng-invalid-required ng-invalid final" required="" rows="3" readonly>'+defaultValue+'</textarea>'+
                    '</div></div>';
            }
            if(question.type === 'multiplechoice' || question.type === "multiselect"){

                question.default = question.default_multiselect || question.default;

                var defaultScopePropertyName =
                    question.variable + '_default';

                if (question.default) {
                    if (question.type === 'multiselect' && typeof question.default.split === 'function') {
                        scope[defaultScopePropertyName] = question.default.split('\n');
                    } else if (question.type !== 'multiselect') {
                        scope[defaultScopePropertyName] = question.default;
                    }
                } else {
                    scope[defaultScopePropertyName] = '';
                }

                html += '<div class="row">';
                html += '<div class="col-xs-8">';
                html += '<div class="SurveyControls-selectWrapper">';
                html += '<survey-question type="' + question.type + '" question="question" ng-required="' + question.required + '" ng-model="' + defaultScopePropertyName + '"></survey-question>';
                html += '</div>';
                html += '</div>';
                html += '</div>';
            }

            if(question.type === 'password'){
              defaultValue = (question.default) ? question.default : "";
              defaultValue = $filter('sanitize')(defaultValue);
              defaultValue = scope.serialize(defaultValue);
              html+='<div class="row">'+
                  ' <div class="col-xs-8 input_area input-group">'+
                  '<span class="input-group-btn">'+
                  '<button class="btn btn-default survey-maker-password show_input_button" id="'+question.variable+'_show_input_button" aw-tool-tip="Toggle the display of plaintext." aw-tip-placement="top" ng-click="toggleInput(&quot;#'+question.variable+'&quot;)" data-original-title="" title="">ABC</button>'+
                  '</span>'+
                  '<input id="'+ question.variable +'" type="password" ng-model="default_password" name="'+ question.variable +'" class="form-control ng-pristine ng-valid-api-error ng-invalid" autocomplete="false" readonly>'+
                  '</div>'+
                  '</div>';
            }

            if(question.type === 'integer'){
                min = (!Empty(question.min)) ? question.min : "";
                max = (!Empty(question.max)) ? question.max : "" ;
                defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_int)) ? question.default_int : "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8 input_area">'+
                    '<input type="number" class="final form-control" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'" readonly>'+
                    '</div></div>';

            }
            if(question.type === "float"){
                min = (!Empty(question.min)) ? question.min : "";
                max = (!Empty(question.max)) ? question.max : "" ;
                defaultValue = (!Empty(question.default)) ? question.default : (!Empty(question.default_float)) ? question.default_float : "" ;
                html+='<div class="row">'+
                    '<div class="col-xs-8 input_area">'+
                    '<input type="number" class="final form-control" name="'+question.variable+'" min="'+min+'" max="'+max+'" value="'+defaultValue+'" readonly>'+
                    '</div></div>';

            }
            html += '<div class="col-xs-12 text-right question_actions">';
            html += '<a id="edit-question_'+question.index+'" data-placement="top" aw-tool-tip="Edit question" data-original-title="" title=""><i class="fa fa-pencil"></i> </a>';
            html += '<a id="delete-question_'+question.index+'" data-placement="top" aw-tool-tip="Delete question" data-original-title="" title=""><i class="fa fa-trash-o"></i> </a>';
            html += '<a id="question-up_'+question.index+'" data-placement="top" aw-tool-tip="Move up" data-original-title="" title=""><i class="fa fa-arrow-up"></i> </a>';
            html += '<a id="question-down_'+question.index+'" data-placement="top" aw-tool-tip="Move down" data-original-title="" title=""><i class="fa fa-arrow-down"></i> </a>';
            html+='</div></div>';

            $('#question_'+question.index).append(html);

            element = angular.element(document.getElementById('question_'+question.index));
            // // element.html(html);
            //element.css('opacity', 0.7);

            $compile(element)(scope);

            $('#add_question_btn').show();
            $('#add_question_btn').removeAttr('disabled');
            $('#add_question_btn').focus();
            $('#survey_maker_save_btn').removeAttr('disabled');

            // Sometimes the $event.target returns the anchor element that wraps the icon, and sometimes the icon itself
            // is returned. So for each icon click event we check to see which target the user clicked, and depending no which one
            // they clicked, we move up the dom hierarchy to get the index on the question. Ultimatley the object that is passed to
            // each one of these functions should be the index of the question that the user is trying to perform an action on.
            $('#delete-question_'+question.index+'').on('click', function($event){
                if($event.target.nodeName==="A"){
                    scope.deleteQuestion($event.target.parentElement.parentElement.id.split('_')[1]);
                }
                else if($event.target.nodeName === "I"){
                    scope.deleteQuestion($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
                }
            });
            $('#edit-question_'+question.index+'').on('click', function($event){
                if($event.target.nodeName==="A"){
                    scope.editQuestion($event.target.parentElement.parentElement.id.split('_')[1]);
                }
                else if($event.target.nodeName === "I"){
                    scope.editQuestion($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
                }
            });
            $('#question-up_'+question.index+'').on('click', function($event){
                if($event.target.nodeName==="A"){
                    scope.questionUp($event.target.parentElement.parentElement.id.split('_')[1]);
                }
                else if($event.target.nodeName === "I"){
                    scope.questionUp($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
                }
            });
            $('#question-down_'+question.index+'').on('click', function($event){
                if($event.target.nodeName==="A"){
                    scope.questionDown($event.target.parentElement.parentElement.id.split('_')[1]);
                }
                else if($event.target.nodeName === "I"){
                    scope.questionDown($event.target.parentElement.parentElement.parentElement.id.split('_')[1]);
                }

            });
        };
    }

FinalizeQuestion.$inject =
    [   'GetBasePath',
        'Rest',
        'Wait',
        'ProcessErrors',
        '$compile',
        'Empty',
        '$filter',
        'questionScope'
    ];
