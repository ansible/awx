/* jshint unused: vars */
export default
    [   '$filter',
        'templateUrl',
        '$location',
        function JobsList($filter, templateUrl, $location) {
        return {
            restrict: 'E',
            link: link,
            scope: {
                data: '='
            },
            templateUrl: templateUrl('dashboard/lists/jobs/jobs-list')
        };

        function link(scope, element, attr) {
            scope.$watch("data", function(data) {
                if (data) {
                    if (data.length > 0) {
                        createList(data);
                        scope.noJobs = false;
                    } else {
                        scope.noJobs = true;
                    }
                }
            });

            function createList(list) {
                // detailsUrl, status, name, time
                scope.jobs = _.map(list, function(job){
                return {
                    detailsUrl: job.url.replace("api/v1", "#"),
                    status: job.status,
                    name: job.name,
                    id: job.id,
                    templateId: job.job_template,
                    time: $filter('longDate')(job.finished)
                }; });

                scope.snapRows = (list.length < 4);
            }

            scope.isSuccessful = function (status) {
                return (status === "successful");
            };

            scope.editJobTemplate = function (jobTemplateId) {
                $location.path( '/job_templates/' + jobTemplateId);
            };
        }
}];
