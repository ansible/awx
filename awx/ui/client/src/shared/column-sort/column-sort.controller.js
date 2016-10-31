export default ['$scope', '$state', 'QuerySet', 'GetBasePath',
    function($scope, $state, qs, GetBasePath) {

        let queryset, path,
            order_by = $state.params[`${$scope.columnIterator}_search`].order_by,
            activeField = isDescending(order_by) ? order_by.substring(1, order_by.length) : order_by;

        function isDescending(str) {
                if (str){
                    return str.charAt(0) === '-';
                }
                else{
                    // default to ascending order if none is supplied
                    return false;
                }
        }
        function invertOrderBy(str) {
            return order_by.charAt(0) === '-' ? `${str.substring(1, str.length)}` : `-${str}`;
        }
        $scope.orderByIcon = function() {
            // column sort is inactive
            if (activeField !== $scope.columnField) {
                return 'fa-sort';
            }
            // column sort is active (governed by order_by) and descending
            else if (isDescending(order_by)) {
                return 'fa-sort-down';
            }
            // column sort is active governed by order_by) and asscending
            else {
                return 'fa-sort-up';
            }
        };

        $scope.toggleColumnOrderBy = function() {
            // toggle active sort order
            if (activeField === $scope.columnField) {
                order_by = invertOrderBy(order_by);
            }
            // set new active sort order
            else {
                order_by = $scope.columnField;
            }
            queryset = _.merge($state.params[`${$scope.columnIterator}_search`], { order_by: order_by });
            path = GetBasePath($scope.basePath) || $scope.basePath;
            $state.go('.', { [$scope.iterator + '_search']: queryset });
            qs.search(path, queryset).then((res) =>{
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
        };

    }
];
