export default ['$scope', '$stateParams', '$state', '$filter', 'GetBasePath', 'QuerySet',
    function($scope, $stateParams, $state, $filter, GetBasePath, qs) {

        let pageSize = $stateParams[`${$scope.iterator}_search`].page_size || 20,
            queryset, path;
        $scope.pageSize = pageSize;

        function init() {
            $scope.pageRange = calcPageRange($scope.current(), $scope.last());
            $scope.dataRange = calcDataRange();
        }
        $scope.dataCount = function() {
            return $filter('number')($scope.dataset.count);
        };

        $scope.toPage = function(page) {
            path = GetBasePath($scope.basePath) || $scope.basePath;
            queryset = _.merge($stateParams[`${$scope.iterator}_search`], { page: page });
            $state.go('.', {
                [$scope.iterator + '_search']: queryset
            });
            qs.search(path, queryset).then((res) => {
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
            $scope.pageRange = calcPageRange($scope.current(), $scope.last());
            $scope.dataRange = calcDataRange();
        };

        $scope.current = function() {
            return parseInt($stateParams[`${$scope.iterator}_search`].page || '1');
        };

        $scope.last = function() {
            return Math.ceil($scope.dataset.count / pageSize);
        };

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
            if ($scope.current() == 1 && $scope.dataset.count < parseInt(pageSize)) {
                return `1 - ${$scope.dataset.count}`;
            } else if ($scope.current() == 1) {
                return `1 - ${pageSize}`;
            } else {
                let floor = (($scope.current() - 1) * parseInt(pageSize)) + 1;
                let ceil = floor + parseInt(pageSize);
                return `${floor} - ${ceil}`;
            }
        }

        init();
    }
];
