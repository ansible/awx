export default [ '$scope', 'Wait', 'Empty', 'Rest', 'ProcessErrors', '$state',
    function($scope, Wait, Empty, Rest, ProcessErrors, $state) {

        $scope.gatherSourceJobs = function(event) {
            if (!Empty($scope.inventory.id)) {
                Wait('start');
                Rest.setUrl($scope.inventory.related.inventory_sources + '?order_by=-last_job_run&page_size=5');
                Rest.get()
                    .then(({data}) => {
                        $scope.generateTable(data, event);
                    })
                    .catch(({data, status}) => {
                        ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + $scope.inventory.related.inventory_sources + ' failed. GET returned status: ' + status
                        });
                    });
            }
        };

        $scope.viewJob = function(url) {
            // Pull the id out of the URL
            var id = url.replace(/^\//, '').split('/')[3];
            $state.go('output', { id, type: 'inventory' } );
        };

    }
];
