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
                disableSearch: '=',
                defaultParams: '=',
                querySet: '=',
                singleSearchParam: '@'
            },
            controller: 'SmartSearchController',
            templateUrl: templateUrl('shared/smart-search/smart-search')
        };
    }
];
