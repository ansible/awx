/* jshint unused: vars */
export default
    [   'InitiatePlaybookRun',
        'templateUrl',
        '$state',
        'Alert',
        function JobTemplatesList(InitiatePlaybookRun, templateUrl, $state, Alert) {
            return {
                restrict: 'E',
                link: link,
                scope: {
                    data: '='
                },
                templateUrl: templateUrl('home/dashboard/lists/job-templates/job-templates-list')
            };

            function link(scope, element, attr) {
                scope.$watch("data", function(data) {
                    if (data) {
                        if (data.length > 0) {
                            createList(data);
                            scope.noJobTemplates = false;
                        } else {
                            scope.noJobTemplates = true;
                        }
                    }
                });

                function createList(list) {
                    // smartStatus?, launchUrl, editUrl, name
                    scope.templates = _.map(list, function(template){ return {
                        recent_jobs: template.summary_fields.recent_jobs,
                        name: template.name,
                        id: template.id,
                        type: template.type
                    }; });
                }

                scope.isSuccessful = function (status) {
                    return (status === "successful");
                };

                scope.launchTemplate = function(template){
                    if(template) {
                            if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                                InitiatePlaybookRun({ scope: scope, id: template.id, job_type: 'job_template' });
                            }
                            else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                                InitiatePlaybookRun({ scope: scope, id: template.id, job_type: 'workflow_job_template' });
                            }
                            else {
                                // Something went wrong - Let the user know that we're unable to launch because we don't know
                                // what type of job template this is
                                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while launching.');
                            }
                        }
                        else {
                            Alert('Error: Unable to launch template', 'Template parameter is missing');
                        }
                };

                scope.editTemplate = function (template) {
                    if(template) {
                        if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                            $state.go('templates.editJobTemplate', {job_template_id: template.id});
                        }
                        else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                            $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: template.id});
                        }
                    }
                };
            }
}];
