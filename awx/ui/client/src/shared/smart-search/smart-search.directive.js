export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'E',
            replace: false,
            transclude: {
                actions: '?div' // preferably would transclude an actions directive here
            },
            scope: {
                djangoModel: '@',
                searchSize: '@',
                basePath: '@',
                iterator: '@',
                list: '=',
                dataset: '=',
                collection: '=',
                searchTags: '=',
            },
            controller: 'SmartSearchController',
            templateUrl: templateUrl('shared/smart-search/smart-search')
        };
    }
];
