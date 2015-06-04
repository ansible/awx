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
                    moment,
                    _) {
    // var inventoryId = $routeParams.id;
    var hostIds = $routeParams.hosts.split(',');
    var hosts = $routeParams.model.hosts;

    $scope.hostIds = $routeParams.hosts;
    $scope.inventory = $routeParams.model.inventory;

    $scope.factModulePickersLabelLeft = "Compare facts collected on or before";
    $scope.factModulePickersLabelRight = "To facts collected on or before";

    $scope.modules = initialFactData.moduleOptions;

    var searchConfig =
        {   leftRange: initialFactData.leftSearchRange,
            rightRange: initialFactData.rightSearchRange
        };

    $scope.leftDate = initialFactData.leftSearchRange.from;
    $scope.rightDate = initialFactData.rightSearchRange.from;

    $scope.leftScanDate = initialFactData.leftScanDate;
    $scope.rightScanDate = initialFactData.rightScanDate;

    $scope.leftHostname = hosts[0].name;
    $scope.rightHostname = hosts.length > 1 ? hosts[1].name : hosts[0].name;

    function reloadData(params, initialData) {

        searchConfig = _.assign({}, searchConfig, params);

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
                    .then(function(factDataAndModules) {
                        var responses = factDataAndModules[1];
                        var data = _.pluck(responses, 'fact');

                        $scope.leftScanDate = moment(responses[0].timestamp);
                        $scope.rightScanDate = moment(responses[1].timestamp);

                        return data;
                    }, true);
        }

        waitIndicator('start');

        return _(factData)
            .promise()
            .then(function(facts) {
                // Make sure we always start comparison against
                // a non-empty array
                //
                // Partition with _.isEmpty will give me an array
                // with empty arrays in index 0, and non-empty
                // arrays in index 1
                //

                // Save the position of the data so we
                // don't lose it later

                facts[0].position = 'left';
                facts[1].position = 'right';

                var splitFacts = _.partition(facts, _.isEmpty);
                var emptyScans = splitFacts[0];
                var nonEmptyScans = splitFacts[1];

                if (_.isEmpty(nonEmptyScans)) {
                    // we have NO data, throw an error
                    throw {
                        name: 'NoScanData',
                        message: 'No scans ran on eithr of the dates you selected. Please try selecting different dates.',
                        dateValues:
                            {   leftDate: $scope.leftDate.clone(),
                                rightDate: $scope.rightDate.clone()
                            }
                    };
                } else if (nonEmptyScans.length === 1) {
                    // one of them is not empty, throw an error
                    throw {
                        name: 'InsufficientScanData',
                        message: 'No scans ran on one of the selected dates. Please try selecting a different date.',
                        dateValue: emptyScans[0].position === 'left' ? $scope.leftDate.clone() : $scope.rightDate.clone()
                    };
                }

                delete facts[0].position;
                delete facts[1].position;

                // all scans have data, rejoice!
                return facts;

            })
            .then(_.partial(compareFacts, _.log('activeModule', activeModule)))
            .then(function(info) {

                // Clear out any errors from the previous run...
                $scope.error = null;

                $scope.factData =  info;

                return info;

            }).finally(function() {
                waitIndicator('stop');
            });
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

        reloadData({   module: newModule
                   }, initialData)

            .catch(function(error) {
                $scope.error = error;
            }).value();
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

                reloadData(params)
                    .catch(function(error) {
                        $scope.error = error;
                    }).value();
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
        'moment',
        'lodashAsPromised',
        controller
    ];
