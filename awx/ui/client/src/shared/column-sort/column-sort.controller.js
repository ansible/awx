export default ['$scope', '$state', 'QuerySet', 'GetBasePath', '$stateParams', '$interpolate',
    function($scope, $state, qs, GetBasePath, $stateParams, $interpolate) {

        let queryset, path;

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
            return str.charAt(0) === '-' ? `${str.substring(1, str.length)}` : `-${str}`;
        }
        $scope.orderByIcon = function() {
            let order_by = $scope.querySet ? $scope.querySet.order_by : $state.params[`${$scope.columnIterator}_search`].order_by;
            // column sort is inactive
            if (order_by !== $scope.columnField && order_by !== invertOrderBy($scope.columnField)) {
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
            let order_by = $scope.querySet ? $scope.querySet.order_by : $state.params[`${$scope.columnIterator}_search`].order_by;

            if (order_by === $scope.columnField || order_by === invertOrderBy($scope.columnField)) {
                order_by = invertOrderBy(order_by);
            }
            // set new active sort order
            else {
                order_by = $scope.columnField;
            }
            if($scope.querySet) {
                // merging $scope.querySet seems to destroy our initial reference which
                // kills the two-way binding here.  To fix that, clone the queryset first
                // and merge with that object.
                let origQuerySet = _.cloneDeep($scope.querySet);
                queryset = _.merge(origQuerySet, { order_by: order_by });
            }
            else {
                queryset = _.merge($state.params[`${$scope.columnIterator}_search`], { order_by: order_by });
            }
            if (GetBasePath($scope.basePath) || $scope.basePath) {
                path = GetBasePath($scope.basePath) || $scope.basePath;
            } else {
                let interpolator = $interpolate($scope.basePath);
                path = interpolator({ $stateParams: $stateParams });
            }
            if(!$scope.querySet) {
                $state.go('.', { [$scope.columnIterator + '_search']: queryset }, {notify: false});
            }
            qs.search(path, queryset).then((res) =>{
                if($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
        };

    }
];
