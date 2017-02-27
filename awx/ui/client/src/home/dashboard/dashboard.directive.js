/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                templateUrl: templateUrl('home/dashboard/dashboard'),
                link: function(scope, element, attrs) {
                }
            };
        }
    ];
