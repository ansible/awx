export default ['templateUrl', function(templateUrl) {
    return {
        restrict: 'E',
        scope: {
            hostFilter: '='
        },
        templateUrl: templateUrl('inventories/smart-inventory/smart-inventory-host-filter/host-filter-modal/host-filter-modal'),
        link: function(scope, element) {

            $('#host-filter-modal').on('hidden.bs.modal', function () {
                $('#host-filter-modal').off('hidden.bs.modal');
                $(element).remove();
            });

            scope.showModal = function() {
                $('#host-filter-modal').modal('show');
            };

            scope.destroyModal = function() {
                $('#host-filter-modal').modal('hide');
            };

        },
        controller: ['$scope', 'QuerySet', 'GetBasePath', 'HostsList', '$compile', 'generateList', function($scope, qs, GetBasePath, HostsList, $compile, GenerateList) {

            function init() {

                $scope.host_default_params = {
                    order_by: 'name',
                    page_size: 5
                };

                $scope.host_queryset = _.merge({
                    order_by: 'name',
                    page_size: 5
                }, $scope.hostFilter ? $scope.hostFilter : {});

                // Fire off the initial search
                qs.search(GetBasePath('hosts'), $scope.host_queryset)
                    .then(res => {
                        $scope.host_dataset = res.data;
                        $scope.hosts = $scope.host_dataset.results;

                        let hostList = _.cloneDeep(HostsList);
                        delete hostList.fields.toggleHost;
                        delete hostList.fields.active_failures;
                        delete hostList.fields.inventory;
                        hostList.well = false;
                        let html = GenerateList.build({
                            list: hostList,
                            input_type: 'host-filter-modal-body',
                            //mode: 'lookup'
                        });

                        $scope.list = hostList;

                        $('#host-filter-modal-body').append($compile(html)($scope));

                        $scope.showModal();
                    });
            }

            init();

            $scope.cancelForm = function() {
                $scope.destroyModal();
            };

            $scope.saveForm = function() {
                // Strip defaults out of the state params copy
                angular.forEach(Object.keys($scope.host_default_params), function(value) {
                    delete $scope.host_queryset[value];
                });

                $scope.hostFilter = angular.copy($scope.host_queryset);

                $scope.destroyModal();
            };

        }]
    };
}];
