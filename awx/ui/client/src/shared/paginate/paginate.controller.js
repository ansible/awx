export default ['$scope', '$stateParams', '$state', 'GetBasePath', 'QuerySet', '$interpolate',
    function($scope, $stateParams, $state, GetBasePath, qs, $interpolate) {

        let pageSize = $scope.querySet ? $scope.querySet.page_size || 20 : $stateParams[`${$scope.iterator}_search`].page_size || 20,
            queryset, path;

        $scope.pageSize = pageSize;
        $scope.basePageSize = parseInt(pageSize) === 5 ? 5 : 20;
        $scope.maxVisiblePages = $scope.maxVisiblePages ? parseInt($scope.maxVisiblePages) : 10;

        $scope.filter = function(id){
            let pageSize = Number(id);
            $('#period-dropdown')
                .replaceWith("<a id=\"period-dropdown\" class=\"DashboardGraphs-filterDropdownText DashboardGraphs-filterDropdownItems--period\" role=\"button\" data-toggle=\"dropdown\" data-target=\"#\" href=\"/page.html\">"+id+
            "<i class=\"fa fa-angle-down DashboardGraphs-filterIcon\"></i>\n");

            if ($scope.querySet){
                $scope.querySet = _.merge($scope.querySet, { page_size: `${pageSize}`});
            } else {
                $scope.querySet = _.merge($stateParams[`${$scope.iterator}_search`], { page_size: `${pageSize}`});
            }
            $scope.toPage(1);
        };

        $scope.toPage = function(page) {
            if (page === 0 || page > $scope.last) {
                return;
            }
            if (GetBasePath($scope.basePath) || $scope.basePath) {
                path = GetBasePath($scope.basePath) || $scope.basePath;
            } else {
                let interpolator = $interpolate($scope.basePath);
                path = interpolator({ $stateParams: $stateParams });
            }
            if ($scope.querySet) {
                // merging $scope.querySet seems to destroy our initial reference which
                // kills the two-way binding here.  To fix that, clone the queryset first
                // and merge with that object.
                let origQuerySet = _.cloneDeep($scope.querySet);
                queryset = _.merge(origQuerySet, { page: page });

            } else {
                let origStateParams = _.cloneDeep($stateParams[`${$scope.iterator}_search`]);
                queryset = _.merge(origStateParams, { page: page });
            }
            if (!$scope.querySet) {
                $state.go('.', {
                    [$scope.iterator + '_search']: queryset
                }, {notify: false});
            }
            qs.search(path, queryset).then((res) => {
                if ($scope.querySet) {
                    // Update the query set
                    $scope.querySet = queryset;
                }
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
                $scope.$emit('updateDataset', res.data, queryset);
            });
            $('html, body').animate({scrollTop: 0}, 0);
        };

        function calcLast() {
            return Math.ceil($scope.dataset.count / $scope.pageSize);
        }

        function calcCurrent() {
            if ($scope.querySet) {
                return parseInt($scope.querySet.page || '1');
            } else {
                return parseInt($stateParams[`${$scope.iterator}_search`].page || '1');
            }
        }

        function calcPageRange(current, last) {
            let result = [],
                maxVisiblePages = parseInt($scope.maxVisiblePages),
                pagesLeft,
                pagesRight;
            if (maxVisiblePages % 2) {
                // It's an odd number
                pagesLeft = (maxVisiblePages - 1) / 2;
                pagesRight = ((maxVisiblePages - 1) / 2) + 1;
            } else {
                // Its an even number
                pagesLeft = pagesRight = maxVisiblePages / 2;
            }
            if (last < maxVisiblePages) {
                // Don't have enough pages to exceed the max range - just show all of them
                result = _.range(1, last + 1);
            } else if (current === last) {
                 result = _.range(last + 1 - maxVisiblePages, last + 1);
            } else {
                let topOfRange = current + pagesRight > maxVisiblePages + 1 ? (current + pagesRight < last + 1 ? current + pagesRight : last + 1) : maxVisiblePages + 1;
                let bottomOfRange = (topOfRange === last + 1) ? last + 1 - maxVisiblePages : (current - pagesLeft > 0 ? current - pagesLeft : 1);
                result = _.range(bottomOfRange, topOfRange);
            }
            return result;
        }

        function calcDataRange() {
            if ($scope.current === 1 && $scope.dataset.count < parseInt($scope.pageSize)) {
                return `1 - ${$scope.dataset.count}`;
            } else if ($scope.current === 1) {
                return `1 - ${$scope.pageSize}`;
            } else {
                let floor = (($scope.current - 1) * parseInt($scope.pageSize)) + 1;
                let ceil = floor + parseInt($scope.pageSize) - 1 < $scope.dataset.count ? floor + parseInt($scope.pageSize) - 1 : $scope.dataset.count;
                return `${floor} - ${ceil}`;
            }
        }

        function calcPageSize(){
            let pageSize = $scope.querySet ? $scope.querySet.page_size || 20 : $stateParams[`${$scope.iterator}_search`].page_size || 20;
            return Number(pageSize) ;
        }

        let updatePaginationVariables = function() {
            $scope.pageSize = calcPageSize();
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
];
