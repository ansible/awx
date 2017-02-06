export default ['$scope', '$stateParams', '$state', '$filter', 'GetBasePath', 'QuerySet',
    function($scope, $stateParams, $state, $filter, GetBasePath, qs) {

        let pageSize,
            queryset, path;

        // TODO: can we clean this if/else up?
        if($scope.querySet) {
            pageSize = $scope.querySet.page_size || 20;
        }
        else {
            // Pull the page size from the url
            pageSize = $stateParams[`${$scope.iterator}_search`].page_size || 20;
        }

        $scope.pageSize = pageSize;

        function init() {

            let updatePaginationVariables = function() {
                $scope.current = calcCurrent();
                $scope.last = calcLast();
                $scope.pageRange = calcPageRange($scope.current, $scope.last);
                $scope.dataRange = calcDataRange();
            };

            updatePaginationVariables();

            $scope.$watch('collection', function(){
                updatePaginationVariables();
            });
        }

        $scope.dataCount = function() {
            return $filter('number')($scope.dataset.count);
        };

        $scope.toPage = function(page) {
            if(page === 0) {
                return;
            }
            path = GetBasePath($scope.basePath) || $scope.basePath;
            if($scope.querySet) {
                // merging $scope.querySet seems to destroy our initial reference which
                // kills the two-way binding here.  To fix that, clone the queryset first
                // and merge with that object.
                let origQuerySet = _.cloneDeep($scope.querySet);
                queryset = _.merge(origQuerySet, { page: page });

            }
            else {
                queryset = _.merge($stateParams[`${$scope.iterator}_search`], { page: page });
            }
            if(!$scope.querySet) {
                $state.go('.', {
                    [$scope.iterator + '_search']: queryset
                }, {notify: false});
            }
            qs.search(path, queryset).then((res) => {
                if($scope.querySet) {
                    // Update the query set
                    $scope.querySet = queryset;
                }
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
            $scope.pageRange = calcPageRange($scope.current, $scope.last);
            $scope.dataRange = calcDataRange();
        };

        function calcLast() {
            return Math.ceil($scope.dataset.count / pageSize);
        }

        function calcCurrent() {
            if($scope.querySet) {
                return parseInt($scope.querySet.page || '1');
            }
            else {
                return parseInt($stateParams[`${$scope.iterator}_search`].page || '1');
            }
        }

        function calcPageRange(current, last) {
            let result = [];
            if (last < 10) {
                result = _.range(1, last + 1);
            } else if (current - 5 > 0 && current !== last) {
                result = _.range(current - 5, current + 6);
            } else if (current === last) {
                result = _.range(last - 10, last + 1);
            } else {
                result = _.range(1, 11);
            }
            return result;
        }

        function calcDataRange() {
            if ($scope.current === 1 && $scope.dataset.count < parseInt(pageSize)) {
                return `1 - ${$scope.dataset.count}`;
            } else if ($scope.current === 1) {
                return `1 - ${pageSize}`;
            } else {
                let floor = (($scope.current - 1) * parseInt(pageSize)) + 1;
                let ceil = floor + parseInt(pageSize) < $scope.dataset.count ? floor + parseInt(pageSize) : $scope.dataset.count;
                return `${floor} - ${ceil}`;
            }
        }

        init();
    }
];
