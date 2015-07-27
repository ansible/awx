/* jshint unused: vars */
export default
    [   "PlaybookRun",
        'templateUrl',
        function JobTemplatesList(PlaybookRun, templateUrl) {
            return {
                restrict: 'E',
                link: link,
                scope: {
                    data: '='
                },
                templateUrl: templateUrl('dashboard/lists/job-templates/job-templates-list')
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
                    scope.job_templates = _.map(list, function(job_template){ return {
                        recent_jobs: job_template.summary_fields.recent_jobs,
                        launch_url: job_template.url,
                        edit_url: job_template.url.replace('api/v1', '#'),
                        name: job_template.name,
                        id: job_template.id
                    }; });

                    scope.snapRows = (list.length < 4);
                }

                scope.isSuccessful = function (status) {
                    return (status === "successful");
                };

                scope.launchJobTemplate = function(jobTemplateId){
                    PlaybookRun({ scope: scope, id: jobTemplateId });
                };
            }
}];
