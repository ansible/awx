export default ['templateUrl',
    function(templateUrl) {
        return {
            restrict: 'E',
            replace: false,
            scope: {
                collection: '=',
                dataset: '=',
                iterator: '@',
                basePath: '@',
                querySet: '=?',
                maxVisiblePages: '@',
                hideViewPerPage: '='
            },
            controller: 'PaginateController',
            templateUrl: templateUrl('shared/paginate/paginate')
        };
    }
];
