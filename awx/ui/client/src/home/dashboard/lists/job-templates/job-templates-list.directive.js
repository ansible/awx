/* jshint unused: vars */
export default
    ['templateUrl', '$state', 'Rest', 'GetBasePath',
    function JobTemplatesList(templateUrl, $state, Rest, GetBasePath)  {
            return {
                restrict: 'E',
                link: link,
                scope: {
                    data: '='
                },
                templateUrl: templateUrl('home/dashboard/lists/job-templates/job-templates-list')
            };

            function link(scope) {

                scope.$watch("data", function(data) {
                    if (data) {
                        if (data.length > 0) {
                            createList(data);
                            scope.noJobTemplates = false;
                        } else {
                            scope.noJobTemplates = true;
                        }
                    }
                }, true);

                scope.canAddJobTemplate = false;
                let url = GetBasePath('job_templates');
                Rest.setUrl(url);
                Rest.options()
                    .then(({ data }) => {
                        if (!data.actions.POST) {
                            scope.canAddJobTemplate = false;
                        } else {
                            scope.canAddJobTemplate = true;
                        }
                    });

                function createList(list) {
                    // smartStatus?, launchUrl, editUrl, name
                    scope.templates = _.map(list, function(template){ return {
                        recent_jobs: template.summary_fields.recent_jobs,
                        can_start: template.summary_fields.user_capabilities.start,
                        name: template.name,
                        id: template.id,
                        type: template.type,
                        can_edit: template.summary_fields.user_capabilities.edit
                    }; });
                }

                scope.isSuccessful = function (status) {
                    return (status === "successful");
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
