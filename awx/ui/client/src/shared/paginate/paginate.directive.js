export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'E',
            replace: false,
            scope: {
                collection: '=',
                dataset: '=',
                iterator: '@',
                basePath: '@'
            },
            controller: 'PaginateController',
            templateUrl: templateUrl('shared/paginate/paginate')
        };
    }
];
