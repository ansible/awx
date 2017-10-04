export default
    function GetSurveyQuestions($filter, GetBasePath, Rest, Empty, ProcessErrors, $stateParams) {

            // This factory goes out and gets a job template's survey questions and attaches
            // them to scope so that they can be ng-repeated in the job submission template

            return function(params) {
                var id= params.id,
                scope = params.scope,
                submitJobType = params.submitJobType,
                i,
                survey_url;

                if(submitJobType === 'job_template') {
                    survey_url = GetBasePath('job_templates') + id + '/survey_spec/';
                }
                else if(submitJobType === 'workflow_job_template') {
                    survey_url = GetBasePath('workflow_job_templates') + id + '/survey_spec/';
                }

                Rest.setUrl(survey_url);
                Rest.get()
                .then(({data}) => {
                    if(!Empty(data)){
                        scope.survey_name = data.name;
                        scope.survey_description = data.description;
                        scope.survey_questions = data.spec;

                        for(i=0; i<scope.survey_questions.length; i++){
                            var question = scope.survey_questions[i];
                            question.index = i;
                            question.question_name = $filter('sanitize')(question.question_name);
                            question.question_description = (question.question_description) ? $filter('sanitize')(question.question_description) : undefined;

                            if(question.type === "textarea" && !Empty(question.default_textarea)) {
                                question.model = angular.copy(question.default_textarea);
                            }
                            else if(question.type === "multiselect") {
                                question.model = question.default.split(/\n/);
                                question.choices = question.choices.split(/\n/);
                            }
                            else if(question.type === "multiplechoice") {
                                question.model = question.default ? angular.copy(question.default) : "";
                                question.choices = question.choices.split(/\n/);

                                // Add a default empty string option to the choices array.  If this choice is
                                // selected then the extra var will not be sent when we POST to the launch
                                // endpoint
                                if(!question.required) {
                                    question.choices.unshift('');
                                }
                            }
                            else if(question.type === "float"){
                                question.model = (!Empty(question.default)) ? angular.copy(question.default) : (!Empty(question.default_float)) ? angular.copy(question.default_float) : "";
                            }
                            else {
                                question.model = question.default ? angular.copy(question.default) : "";
                            }

                            if(question.type === "text" || question.type === "textarea" || question.type === "password") {
                                question.minlength = (!Empty(question.min)) ? Number(question.min) : "";
                                question.maxlength = (!Empty(question.max)) ? Number(question.max) : "" ;
                            }
                            else if(question.type === "integer") {
                                question.minValue = (!Empty(question.min)) ? Number(question.min) : "";
                                question.maxValue = (!Empty(question.max)) ? Number(question.max) : "" ;
                            }
                            else if(question.type === "float") {
                                question.minValue = (!Empty(question.min)) ? question.min : "";
                                question.maxValue = (!Empty(question.max)) ? question.max : "" ;
                            }
                        }

                        return;
                    }
                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, { hdr: 'Error!',
                    msg: 'Failed to retrieve organization: ' + $stateParams.id + '. GET status: ' + status });
                });

            };
        }

GetSurveyQuestions.$inject =
    [   '$filter',
        'GetBasePath',
        'Rest' ,
        'Empty',
        'ProcessErrors',
        '$stateParams'
    ];
