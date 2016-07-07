/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                templateUrl: templateUrl('access/roleList'),
                link: function(scope, element, attrs) {
                    // given a list of roles (things like "project
                    // auditor") which are pulled from two different
                    // places in summary fields, and creates a
                    // concatenated/sorted list
                    scope.access_list = []
                        .concat(scope.permission.summary_fields
                            .direct_access.map((i) => {
                                i.role.explicit = true;
                                return i.role;
                        }))
                        .concat(scope.permission.summary_fields
                            .indirect_access.map((i) => {
                                i.role.explicit = false;
                                return i.role;
                        }))
                        .filter((role) => {
                            return !!attrs.teamRoleList == !!role.team_id;
                        })
                        .sort((a, b) => {
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
