/**
 * Delete a survey. Prompts user to confirm delete
 *
 * DeleteSurvey({
 *     scope:       $scope containing list of survey form fields
 *     id:          id of job template that survey is attached to
 * })
 *
 */
export default
    function DeleteSurvey(GetBasePath, Rest, Wait, ProcessErrors) {
        return function(params) {

            var scope = params.scope,
                id = params.id,
                templateType = params.templateType,
                url;


            if (scope.removeSurveyDeleted) {
                scope.removeSurveyDeleted();
            }
            scope.$on('SurveyDeleted', function(){
                scope.survey_name = "";
                scope.survey_description = "";
                scope.survey_questions = [];
                scope.closeSurvey('survey-modal-dialog');
                Wait('stop');
                scope.survey_exists = false;
            });


            Wait('start');

            if(scope.mode==="add"){
                scope.$emit("SurveyDeleted");

            } else {
                let basePath = templateType === 'workflow_job_template' ? GetBasePath('workflow_job_templates') : GetBasePath('job_templates');
                url = basePath + id + '/survey_spec/';

                Rest.setUrl(url);
                Rest.destroy()
                    .then(() => {
                        scope.$emit("SurveyDeleted");

                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, { hdr: 'Error!',
                            msg: 'Failed to delete survey. DELETE returned status: ' + status });
                    });
            }
        };
    }

DeleteSurvey.$inject =
    [   'GetBasePath',
        'Rest',
        'Wait',
        'ProcessErrors'
    ];
