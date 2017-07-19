export default [ '$scope', 'Empty', 'Wait', 'GetBasePath', 'Rest', 'ProcessErrors', '$state',
    function($scope, Empty, Wait, GetBasePath, Rest, ProcessErrors, $state) {

        $scope.gatherRecentJobs = function(event) {
            if (!Empty($scope.inventory.id)) {
                if ($scope.inventory.total_hosts > 0) {
                    Wait('start');
                    let url = GetBasePath('jobs') + "?type=job&inventory=" + $scope.inventory.id + "&failed=";
                    url += ($scope.inventory.has_active_failures) ? "true" : "false";
                    url += "&order_by=-finished&page_size=5";
                    Rest.setUrl(url);
                    Rest.get()
                        .success( function(data) {
                            $scope.generateTable(data, event);
                        })
                        .error( function(data, status) {
                            ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. GET returned: ' + status
                            });
                        });
                }
            }
        };

        $scope.viewJob = function(jobId) {
            $state.go('jobResult', {id: jobId});
        };

    }
];
