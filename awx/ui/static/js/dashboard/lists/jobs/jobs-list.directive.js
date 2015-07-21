/* jshint unused: vars */
export default
    [   'moment',
        'templateUrl',
        function JobsList(moment, templateUrl) {
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
                    time: moment(job.finished).fromNow()
                }; });

                scope.snapRows = (list.length < 4);
            }

            scope.isSuccessful = function (status) {
                return (status === "successful");
            };
        }
}];
