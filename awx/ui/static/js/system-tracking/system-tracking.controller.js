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
        {   leftRange: initialFactData.leftSearchRange,
            rightRange: initialFactData.rightSearchRange
        };

    $scope.leftDate = initialFactData.leftSearchRange.from;
    $scope.rightDate = initialFactData.rightSearchRange.from;

    function setHeaderValues(viewType) {
        if (viewType === 'singleHost') {
            $scope.comparisonLeftHeader = $scope.leftScanDate;
            $scope.comparisonRightHeader = $scope.rightScanDate;
        } else {
            $scope.comparisonLeftHeader = hosts[0].name;
            $scope.comparisonRightHeader = hosts[1].name;
        }
    }

    function reloadData(params, initialData) {
        searchConfig = _.merge({}, searchConfig, params);

        var factData = initialData;
        var leftRange = searchConfig.leftRange;
        var rightRange = searchConfig.rightRange;
        var activeModule = searchConfig.module;

        if (!factData) {
            factData =
                getDataForComparison(
                            hostIds,
                            activeModule.name,
                            leftRange,
                            rightRange)
                    .thenAll(function(factDataAndModules) {
                        var responses = factDataAndModules[1];
                        var data = _.pluck(responses, 'fact');

                        $scope.leftScanDate = moment(responses[0].timestamp);
                        $scope.rightScanDate = moment(responses[1].timestamp);

                        return data;
                    }, true);
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

    $scope.$watch('leftDate', dateWatcher('leftRange'), true);

    $scope.$watch('rightDate', dateWatcher('rightRange'), true);

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
