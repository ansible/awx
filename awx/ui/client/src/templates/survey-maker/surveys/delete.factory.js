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
                url = GetBasePath('job_templates')+ id + '/survey_spec/';

                Rest.setUrl(url);
                Rest.destroy()
                    .success(function () {
                        scope.$emit("SurveyDeleted");

                    })
                    .error(function (data, status) {
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
