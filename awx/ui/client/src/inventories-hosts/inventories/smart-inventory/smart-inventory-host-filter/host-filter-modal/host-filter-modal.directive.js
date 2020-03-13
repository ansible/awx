export default ['templateUrl', function(templateUrl) {
    return {
        restrict: 'E',
        scope: {
            hostFilter: '=',
            organization: '='
        },
        templateUrl: templateUrl('inventories-hosts/inventories/smart-inventory/smart-inventory-host-filter/host-filter-modal/host-filter-modal'),
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
        controller: ['$scope', 'QuerySet', 'GetBasePath', 'HostsList', '$compile', 'generateList', 'i18n', '$rootScope', function($scope, qs, GetBasePath, HostsList, $compile, GenerateList, i18n, $rootScope) {

            function init() {

                $scope.appStrings = $rootScope.appStrings;

                $scope.host_default_params = {
                    order_by: 'name',
                    page_size: 5,
                    inventory__organization: $scope.organization
                };

                $scope.host_queryset = _.merge({
                    order_by: 'name',
                    page_size: 5,
                    inventory__organization: $scope.organization
                }, $scope.hostFilter ? $scope.hostFilter : {});

                // Fire off the initial search
                qs.search(GetBasePath('hosts'), $scope.host_queryset)
                    .then(res => {
                        $scope.host_dataset = res.data;
                        $scope.hosts = $scope.host_dataset.results;

                        let hostList = _.cloneDeep(HostsList);
                        delete hostList.staticColumns;
                        delete hostList.fields.toggleHost;
                        delete hostList.fields.active_failures;
                        delete hostList.fields.name.ngClick;
                        hostList.fields.name.columnClass = 'col-sm-6';
                        hostList.fields.name.noLink = true;
                        hostList.well = false;
                        delete hostList.fields.inventory.ngClick;
                        hostList.fields.inventory.columnClass = 'col-sm-6';
                        hostList.fields.inventory.ngBind = 'host.summary_fields.inventory.name';
                        hostList.emptyListText = i18n._('Perform a search above to define a host filter');
                        hostList.layoutClass = 'List-defaultLayout';
                        hostList.alwaysShowSearch = true;
                        hostList.emptyListClass = 'List-noItems List-emptyHostFilter';
                        let html = GenerateList.build({
                            list: hostList,
                            input_type: 'host-filter-modal-body',
                            hideViewPerPage: true
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
