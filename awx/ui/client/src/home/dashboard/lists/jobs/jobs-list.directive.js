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
            templateUrl: templateUrl('home/dashboard/lists/jobs/jobs-list')
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
                    detailsUrl: job.type && job.type === 'workflow_job' ? job.url.replace(/api\/v\d+\/workflow_jobs/, "#/workflows") : job.url.replace(/api\/v\d+/, "#"),
                    status: job.status,
                    name: job.name,
                    id: job.id,
                    time: $filter('longDate')(job.finished)
                }; });
            }

            scope.isSuccessful = function (status) {
                return (status === "successful");
            };
        }
}];
