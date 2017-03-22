export default
    function EditQuestion(GenerateForm, CreateSelect2, SurveyQuestionForm) {
        return function(params) {

            var scope = params.scope,
                index = params.index,
                tmpVar,
                i,
                question = params.question,
                form = SurveyQuestionForm;

            // Update the index so that we know which question is being edited.
            scope.editQuestionIndex = index;

            scope.text_min = null;
            scope.text_max = null;
            scope.int_min = null;
            scope.int_max = null;
            scope.float_min = null;
            scope.float_max = null;
            scope.password_min = null;
            scope.password_max = null;
            scope.pwcheckbox = false;

            if (scope.removeFillQuestionForm) {
                scope.removeFillQuestionForm();
            }
            scope.removeFillQuestionForm = scope.$on('FillQuestionForm', function() {
                for( var fld in form.fields){
                    scope[fld] = question[fld];
                    if(form.fields[fld].type === 'select'){
                        for (i = 0; i < scope.answer_types.length; i++) {
                            if (question[fld] === scope.answer_types[i].type) {
                                scope[fld] = scope.answer_types[i];
                            }
                        }
                    }
                }
                if( question.type === 'text'){
                    scope.text_min = question.min;
                    scope.text_max = question.max;
                    scope.default_text = question.default;
                }
                if( question.type === 'textarea'){
                    scope.textarea_min = question.min;
                    scope.textarea_max = question.max;
                    scope.default_textarea= question.default;
                }
                if(question.type === 'password'){
                    scope.password_min = question.min;
                    scope.password_max = question.max;
                    scope.default_password = question.default;
                }
                if( question.type === 'integer'){
                    scope.int_min = question.min;
                    scope.int_max = question.max;
                    scope.default_int = question.default;
                }
                else if( question.type  === 'float'  ) {
                    scope.float_min = question.min;
                    scope.float_max = question.max;
                    scope.default_float = question.default;

                }
                else if ( question.type === 'multiselect'){
                    scope.default_multiselect = question.default;
                }

                // After we populate the form with data, need to call CreateSelect2 again
                // to get the dropdown to show the selected item.
                CreateSelect2({
                    element:'#survey_question_type',
                    multiple: false
                });

                // Set the form to dirty.  This lets the cancel button know that it should become enabled.
                scope.survey_question_form.$setDirty();
            });

            if (scope.removeGenerateForm) {
                scope.removeGenerateForm();
            }
            scope.removeGenerateForm = scope.$on('GenerateForm', function() {
                tmpVar = scope.mode;
                GenerateForm.inject(form, { id: 'survey_maker_question_form', mode: 'edit', related: false, scope:scope, noPanel: true });
                scope.mode = tmpVar;
                scope.$emit('FillQuestionForm');
            });


            scope.$emit('GenerateForm');

        };
    }

EditQuestion.$inject =
    [   'GenerateForm',
        'CreateSelect2',
        'questionDefinitionForm'
    ];
