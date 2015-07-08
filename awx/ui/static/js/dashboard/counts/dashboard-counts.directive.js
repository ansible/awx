/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: {
                    data: '='
                },
                replace: false,
                templateUrl: templateUrl('dashboard/counts/dashboard-counts'),
                link: function(scope, element, attrs) {
                    scope.$watch("data", function(data) {
                        if (data && data.hosts) {
                            createCounts(data);
                        }
                    });

                    function addFailureToCount(val) {
                        if (val.isFailureCount) {
                            // delete isFailureCount
                            if (val.number > 0) {
                                val.isFailure = true;
                            } else {
                                val.isFailure = false;
                            }
                        } else {
                            val.isFailure = false;
                        }
                        return val;
                    }

                    function createCounts(data) {
                        scope.counts = _.map([
                            {
                                url: "/#/home/hosts",
                                number: scope.data.hosts.total,
                                label: "Hosts"
                            },
                            {
                                url: "/#/home/hosts?has_active_failures=true",
                                number: scope.data.hosts.failed,
                                label: "Failed Hosts",
                                isFailureCount: true
                            },
                            {
                                url: "/#/inventories",
                                number: scope.data.inventories.total,
                                label: "Inventories",
                            },
                            {
                                url: "/#/inventories/?inventory_sources_with_failures",
                                number: scope.data.inventories.inventory_failed,
                                label: "Inventory Sync Failures",
                                isFailureCount: true
                            },
                            {
                                url: "/#/projects",
                                number: scope.data.projects.total,
                                label: "Projects"
                            },
                            {
                                url: "/#/projects/?status=failed",
                                number: scope.data.projects.failed,
                                label: "Projects Sync Failures",
                                isFailureCount: true
                            }
                        ], function(val) { return addFailureToCount(val); });
                    }
                }
            };
        }
    ];
