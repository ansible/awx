/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                templateUrl: templateUrl('dashboard/dashboard'),
                link: function(scope, element, attrs) {
                }
            };
        }
    ];
