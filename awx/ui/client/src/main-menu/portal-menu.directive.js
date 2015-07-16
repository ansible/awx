export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                templateUrl: templateUrl('main-menu/menu-portal'),
                link: function(scope, element) {
                    var contents = element.contents();
                    contents.unwrap();

                    scope.$on('$destroy', function() {
                        contents.remove();
                        $(".MenuItem--socketStatus").remove();
                    });
                }
            };
        }
    ];
