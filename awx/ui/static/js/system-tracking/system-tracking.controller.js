/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {searchDateRange} from './search-date-range';
import {compareFacts} from './compare-facts';

function controller($rootScope,
                    $scope,
                    $routeParams,
                    $location,
                    $q,
                    initialFactData,
                    getDataForComparison,
                    waitIndicator,

                    _) {
    // var inventoryId = $routeParams.id;
    var hostIds = $routeParams.hosts.split(',');
    var hosts = $routeParams.model.hosts;

    $scope.hostIds = $routeParams.hosts;
    $scope.inventory = $routeParams.model.inventory;

    $scope.factModulePickersLabelLeft = "Compare facts collected on";
    $scope.factModulePickersLabelRight = "To facts collected on";

    $scope.modules = initialFactData.moduleOptions;

    // Use this to determine how to orchestrate the services
    var viewType = hostIds.length > 1 ? 'multiHost' : 'singleHost';

    var searchConfig =
        {   leftDate: initialFactData.leftDate,
            rightDate: initialFactData.rightDate
        };

    $scope.leftDate = initialFactData.leftDate.from;
    $scope.rightDate = initialFactData.rightDate.from;

    function setHeaderValues(viewType) {
        if (viewType === 'singleHost') {
            $scope.comparisonLeftHeader = $scope.leftDate;
            $scope.comparisonRightHeader = $scope.rightDate;
        } else {
            $scope.comparisonLeftHeader = hosts[0].name;
            $scope.comparisonRightHeader = hosts[1].name;
        }
    }

    function reloadData(params, initialData) {
        searchConfig = _.merge({}, searchConfig, params);

        var factData = initialData;
        var leftDate = searchConfig.leftDate;
        var rightDate = searchConfig.rightDate;
        var activeModule = searchConfig.module;

        if (!factData) {
            factData = getDataForComparison(
                hostIds,
                activeModule.name,
                leftDate,
                rightDate);
        }

        waitIndicator('start');

        _(factData)
            .thenAll(_.partial(compareFacts, activeModule))
            .then(function(info) {

                $scope.factData =  info;

                setHeaderValues(viewType);

            }).finally(function() {
                waitIndicator('stop');
            })
            .value();
    }

    $scope.setActiveModule = function(newModuleName, initialData) {

        var newModule = _.find($scope.modules, function(module) {
            return module.name === newModuleName;
        });

        $scope.modules.forEach(function(module) {
            module.isActive = false;
        });

        newModule.isActive = true;

        $location.replace();
        $location.search('module', newModuleName);

        reloadData(
            {   module: newModule
            }, initialData);
    };

    function dateWatcher(dateProperty) {
        return function(newValue, oldValue) {
                // passing in `true` for the 3rd param to $watch should make
                // angular use `angular.equals` for comparing these values;
                // the watcher should not fire, but it still is. Therefore,
                // using `moment.isSame` to keep from reloading data when the
                // dates did not actually change
                if (newValue.isSame(oldValue)) {
                    return;
                }

                var newDate = searchDateRange(newValue);

                var params = {};
                params[dateProperty] = newDate;

                reloadData(params);
            };
    }

    $scope.$watch('leftDate', dateWatcher('leftDate'), true);

    $scope.$watch('rightDate', dateWatcher('rightDate'), true);

    $scope.setActiveModule(initialFactData.moduleName, initialFactData);
}

export default
    [   '$rootScope',
        '$scope',
        '$routeParams',
        '$location',
        '$q',
        'factScanData',
        'getDataForComparison',
        'Wait',
        'lodashAsPromised',
        controller
    ];
