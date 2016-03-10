/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: false,
                templateUrl: templateUrl('access/roleList'),
                link: function(scope, element, attrs) {
                    // given a list of roles (things like "project
                    // auditor") which are pulled from two different
                    // places in summary fields, and creates a
                    // concatenated/sorted list
                    scope.roles = []
                        .concat(scope.permission.summary_fields
                            .direct_access.map(function(i) {
                                return {
                                    name: i.role.name,
                                    roleId: i.role.id,
                                    resourceName: i.role.resource_name,
                                    explicit: true
                                };
                        }))
                        .concat(scope.permission.summary_fields
                            .indirect_access.map(function(i) {
                                return {
                                    name: i.role.name,
                                    roleId: i.role.id,
                                    explicit: false
                                };
                        }))
                        .sort(function(a, b) {
                            if (a.name
                                .toLowerCase() > b.name
                                    .toLowerCase()) {
                                return 1;
                            } else {
                                return -1;
                            }
                        });
                }
            };
        }
    ];
