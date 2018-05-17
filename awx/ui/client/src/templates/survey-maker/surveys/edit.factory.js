export default
    function EditFactory(ShowSurveyModal, Wait, Rest, ProcessErrors, GetBasePath, Empty, AddSurvey) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                templateType = params.templateType,
                url;

            if(templateType === 'job_template'){
                url = GetBasePath('job_templates') + id + '/survey_spec/';
            }
            else if(templateType === 'workflow_job_template') {
                url = GetBasePath('workflow_job_templates') + id + '/survey_spec/';
            }

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#survey-modal-dialog').dialog('open');
                scope.generateAddQuestionForm();
            });

            Wait('start');
            //for adding a job template:
            if(scope.mode === 'add'){
                ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });
            }
            //editing an existing job template:
            else{
                // Get the existing record
                Rest.setUrl(url);
                Rest.get()
                    .then(({data}) => {
                            if(!Empty(data)){
                                ShowSurveyModal({ title: "Edit Survey", scope: scope, callback: 'DialogReady' });
                                scope.survey_name = data.name;
                                scope.survey_description = data.description;
                                scope.survey_questions = data.spec;
                                scope.isEditSurvey = true;
                                Wait('stop');
                            } else {
                                AddSurvey({
                                    scope: scope
                                });
                            }

                        })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, null,  { hdr: 'Error!',
                            msg: 'Failed to retrieve survey. GET returned status: ' + status });
                    });

            }
        };
    }


EditFactory.$inject =
    [   'showSurvey',
        'Wait',
        'Rest',
        'ProcessErrors',
        'GetBasePath',
        'Empty',
        'addSurvey'
    ];
