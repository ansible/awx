/* jshint unused: vars */
export default
    [   'templateUrl',
        'i18n',
        function(templateUrl, i18n) {
            return {
                restrict: 'E',
                scope: {
                    data: '='
                },
                replace: false,
                templateUrl: templateUrl('home/dashboard/counts/dashboard-counts'),
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
                                url: "/#/hosts",
                                number: scope.data.hosts.total,
                                label: i18n._("Hosts")
                            },
                            {
                                url: "/#/hosts?host_search=last_job_host_summary__failed:true",
                                number: scope.data.hosts.failed,
                                label: i18n._("Failed Hosts"),
                                isFailureCount: true
                            },
                            {
                                url: "/#/inventories",
                                number: scope.data.inventories.total,
                                label: i18n._("Inventories"),
                            },
                            {
                                url: "/#/inventories?inventory_search=inventory_sources_with_failures__gt:0",
                                number: scope.data.inventories.inventory_failed,
                                label: i18n._("Inventory Sync Failures"),
                                isFailureCount: true
                            },
                            {
                                url: "/#/projects",
                                number: scope.data.projects.total,
                                label: i18n._("Projects")
                            },
                            {
                                url: "/#/projects?project_search=status__in:failed,canceled",
                                number: scope.data.projects.failed,
                                label: i18n._("Project Sync Failures"),
                                isFailureCount: true
                            }
                        ], function(val) { return addFailureToCount(val); });
                    }
                }
            };
        }
    ];
