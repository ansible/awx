export default
    function EditFactory($stateParams, SchedulerInit, ShowSurveyModal, Wait, Rest, ProcessErrors, GetBasePath, GenerateForm,
        Empty, AddSurvey) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                tempSurv = {},
                url = GetBasePath('job_templates') + id + '/survey_spec/', i;

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#survey-modal-dialog').dialog('open');
            });

            scope.resetForm();
            Wait('start');
            //for adding a job template:
            if(scope.mode === 'add'){
                tempSurv.survey_name = scope.survey_name;
                tempSurv.survey_description = scope.survey_description;
                tempSurv.survey_questions = scope.survey_questions;

                ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });

                // scope.survey_name = tempSurv.survey_name;
                // scope.survey_description = tempSurv.survey_description;

                for(i=0; i<tempSurv.survey_questions.length; i++){
                    scope.finalizeQuestion(tempSurv.survey_questions[i], i);
                }
            }
            //editing an existing job template:
            else{
                // Get the existing record
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                            if(!Empty(data)){
                                ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });

                                scope.survey_name = data.name;
                                scope.survey_description = data.description;
                                scope.survey_questions = data.spec;
                                for(i=0; i<scope.survey_questions.length; i++){
                                    scope.finalizeQuestion(scope.survey_questions[i], i);
                                }
                                // scope.addQuestion();
                                Wait('stop');
                            } else {
                                AddSurvey({
                                    scope: scope
                                });
                            }

                        })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null,  { hdr: 'Error!',
                            msg: 'Failed to retrieve survey. GET returned status: ' + status });
                    });

            }
        };
    }


EditFactory.$inject =
    [   '$stateParams',
        'SchedulerInit',
        'showSurvey',
        'Wait',
        'Rest',
        'ProcessErrors',
        'GetBasePath',
        'GenerateForm',
        'Empty',
        'addSurvey'
    ];

