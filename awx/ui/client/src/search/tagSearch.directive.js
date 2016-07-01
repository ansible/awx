import tagSearchController from './tagSearch.controller';

/* jshint unused: vars */
export default
    ['templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: {
                  list: '@',
                  endpoint: '@',
                  set: '@',
                  iterator: '@',
                  currentSearchFilters: '='
                },
                controller: tagSearchController,
                templateUrl: templateUrl('search/tagSearch'),
                link: function(scope, element, attrs) {
                    // make the enter button work as if clicking the
                    // search icon
                    element
                        .find('.TagSearch-searchTermInput')
                        .bind('keypress', function (e) {
                            var code = e.keyCode || e.which;
                            if (code === 13) {
                                scope.addTag(e);
                            }
                        });
                }
            };
        }
    ];
