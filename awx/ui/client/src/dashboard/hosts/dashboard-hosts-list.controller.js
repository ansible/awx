/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$state', '$stateParams', 'GetBasePath', 'DashboardHostsList',
    'generateList', 'SetStatus', 'DashboardHostService', '$rootScope', 'Dataset',
    function($scope, $state, $stateParams, GetBasePath, DashboardHostsList,
        GenerateList, SetStatus, DashboardHostService, $rootScope, Dataset) {

        let list = DashboardHostsList;
        init();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.$watchCollection(list.name, function() {
                $scope[list.name] = _.map($scope.hosts, function(value) {
                    value.inventory_name = value.summary_fields.inventory.name;
                    value.inventory_id = value.summary_fields.inventory.id;
                    return value;
                });
                setJobStatus();
            });
        }


        function setJobStatus(){
            _.forEach($scope.hosts, function(value) {
                SetStatus({
                    scope: $scope,
                    host: value
                });
            });
        }

        $scope.editHost = function(id) {
            $state.go('dashboardHosts.edit', { id: id });
        };

        $scope.toggleHostEnabled = function(host) {
            DashboardHostService.setHostStatus(host, !host.enabled)
                .then(function(res) {
                    var index = _.findIndex($scope.hosts, function(o) {
                        return o.id === res.data.id;
                    });
                    $scope.hosts[index].enabled = res.data.enabled;
                });
        };
    }
];
