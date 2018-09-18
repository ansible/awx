/* jshint unused: vars */
export default
    [   '$filter',
        'templateUrl',
        '$location',
        'i18n',
        'JobsStrings',
        function JobsList($filter, templateUrl, $location, i18n, strings) {
        return {
            restrict: 'E',
            link: link,
            scope: {
                data: '='
            },
            templateUrl: templateUrl('home/dashboard/lists/jobs/jobs-list')
        };

        function link(scope, element, attr) {
            scope.strings = strings;
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

                let detailsUrl, tooltip;

                if (job.type === 'workflow_job') {
                    detailsUrl = `/#/workflows/${job.id}`;
                } else {
                    detailsUrl = `/#/jobs/playbook/${job.id}`;
                }
                
                return {
                    detailsUrl,
                    status: job.status,
                    name: job.name,
                    id: job.id,
                    time: $filter('longDate')(job.finished),
                    tooltip: tooltip
                }; });
            }

            scope.isSuccessful = function (status) {
                return (status === "successful");
            };
        }
}];
