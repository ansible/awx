/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {searchDateRange} from './search-date-range';
import {compareFacts} from './compare-facts/main';

function controller($rootScope,
                    $scope,
                    $routeParams,
                    $location,
                    $q,
                    moduleOptions,
                    getDataForComparison,
                    waitIndicator,
                    moment,
                    _) {

    // var inventoryId = $routeParams.id;
    var hostIds = $routeParams.hosts.split(',');
    var hosts = $routeParams.model.hosts;
    var moduleParam = $routeParams.module || 'packages';

    $scope.compareMode =
        hostIds.length === 1 ? 'single-host' : 'host-to-host';
    $scope.hostIds = $routeParams.hosts;
    $scope.inventory = $routeParams.model.inventory;

    if ($scope.compareMode === 'host-to-host') {
        $scope.factModulePickersLabelLeft = "Compare latest facts collected across both hosts on or before";
    } else {
        $scope.factModulePickersLabelLeft = "Compare latest facts collected on or before";
        $scope.factModulePickersLabelRight = "To latest facts collected on or before";
    }

    $scope.modules = moduleOptions;

    var leftSearchRange = searchDateRange();
    var rightSearchRange = searchDateRange();

    var searchConfig =
        {   leftRange: leftSearchRange,
            rightRange: rightSearchRange
        };

    $scope.leftDate = leftSearchRange.from;
    $scope.rightDate = rightSearchRange.from;

    $scope.leftHostname = hosts[0].name;
    $scope.rightHostname = hosts.length > 1 ? hosts[1].name : hosts[0].name;

    function reloadData(params) {

        searchConfig = _.assign({}, searchConfig, params);

        var leftRange = searchConfig.leftRange;
        var rightRange = searchConfig.rightRange;
        var activeModule = searchConfig.module;

        if ($scope.compareMode === 'host-to-host') {
            rightRange = searchConfig.leftRange;
        }

        $scope.leftDataNoScans = false;
        $scope.rightDataNoScans = false;

        waitIndicator('start');

        return getDataForComparison(
                            hostIds,
                            activeModule.name,
                            leftRange,
                            rightRange)
                .then(function(responses) {
                    var data = _.pluck(responses, 'fact');

                    if (_.isEmpty(data[0])) {
                        $scope.leftDataNoScans = true;
                        $scope.leftScanDate = $scope.leftDate;
                    } else {
                        $scope.leftScanDate = moment(responses[0].timestamp);
                    }

                    if (_.isEmpty(data[1])) {
                        $scope.rightDataNoScans = true;
                        $scope.rightScanDate = $scope.rightDate;
                    } else {
                        $scope.rightScanDate = moment(responses[1].timestamp);
                    }

                    return data;
                })

                .then(function(facts) {
                    // Make sure we always start comparison against
                    // a non-empty array
                    //
                    // Partition with _.isEmpty will give me an array
                    // with empty arrays in index 0, and non-empty
                    // arrays in index 1
                    //

                    var wrappedFacts =
                        facts.map(function(facts, index) {
                            return {    position: index === 0 ? 'left' : 'right',
                                        isEmpty: _.isEmpty(facts),
                                        facts: facts
                                   };
                        });

                    var splitFacts = _.partition(facts, 'isEmpty');
                    var emptyScans = splitFacts[0];
                    var nonEmptyScans = splitFacts[1];
                    var result;

                    if (_.isEmpty(nonEmptyScans)) {
                        // we have NO data, throw an error
                        result = _.reject({
                            name: 'NoScanData',
                            message: 'No scans ran on eithr of the dates you selected. Please try selecting different dates.',
                            dateValues:
                                {   leftDate: $scope.leftDate.clone(),
                                    rightDate: $scope.rightDate.clone()
                                }
                        });
                    } else if (nonEmptyScans.length === 1) {
                        // one of them is not empty, throw an error
                        result = _.reject({
                            name: 'InsufficientScanData',
                            message: 'No scans ran on one of the selected dates. Please try selecting a different date.',
                            dateValue: emptyScans[0].position === 'left' ? $scope.leftDate.clone() : $scope.rightDate.clone()
                        });
                    } else {
                        result = _.promise(wrappedFacts);
                    }

                    // all scans have data, rejoice!
                    return result;

                })
                .then(_.partial(compareFacts, activeModule))
                .then(function(info) {

                    // Clear out any errors from the previous run...
                    $scope.error = null;

                    $scope.factData =  info.factData;
                    $scope.isNestedDisplay = info.isNestedDisplay;

                    return info;

                }).catch(function(error) {
                    $scope.error = error;
                }).finally(function() {
                    waitIndicator('stop');
                });
    }

    $scope.setActiveModule = function(newModuleName, initialData) {
        var newModule = _.find($scope.modules, function(module) {
            return module.name === newModuleName;
        });

        if (newModule.isActive) {
            return;
        }

        $scope.modules.forEach(function(module) {
            module.isActive = false;
        });

        newModule.isActive = true;

        $location.replace();
        $location.search('module', newModuleName);

        reloadData({   module: newModule
                   }, initialData).value();
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

                reloadData(params).value();
            };
    }

    $scope.$watch('leftDate', dateWatcher('leftRange'), true);

    $scope.$watch('rightDate', dateWatcher('rightRange'), true);

    $scope.setActiveModule(moduleParam);
}

export default
    [   '$rootScope',
        '$scope',
        '$routeParams',
        '$location',
        '$q',
        'moduleOptions',
        'getDataForComparison',
        'Wait',
        'moment',
        'lodashAsPromised',
        controller
    ];
