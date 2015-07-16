(function (angular) {

    var application = angular.module('application', ['Timezones']);

    application.constant('$timezones.definitions.location', '/tz/data');

    application.controller('World', ['$scope', '$timezones', '$filter',
        function ($scope, $timezones, $filter) {
            
            var now = $scope.now = Date.now();
            
            if ($scope.removeZonesReady) {
                $scope.removeZonesReady();
            }
            $scope.removeZonesReady = $scope.$on('zonesReady', function() {
                var i;
                $scope.zones = JSON.parse(localStorage.zones);
                $scope.current_timezone = $timezones.getLocal();
                for (i=0; i < $scope.zones.length; i++) {
                    if ($scope.zones[i].name === $scope.current_timezone.name) {
                        $scope.selectedZone = $scope.zones[i];
                        break;
                    }
                }
            });

            $scope.zoneChange = function() {
                var date = new Date();
                $scope.current_timezone = $timezones.resolve($scope.selectedZone.name, date);
            };
            
            $timezones.getZoneList($scope);
            
            $scope.examples = [{
                timezone: 'Pacific/Honolulu',
                reference: now
            }, {
                timezone: 'America/Los_Angeles',
                reference: now
            }, {
                timezone: 'America/Chicago',
                reference: now
            }, {
                timezone: 'America/New_York',
                reference: now
            }, {
                timezone: 'Europe/Berlin',
                reference: now
            }, {
                timezone: 'Asia/Tokyo',
                reference: now
            }, {
                timezone: 'Australia/Sydney',
                reference: now
            }, {
                timezone: 'Etc/GMT+12',
                reference: now
            }];
            
        }
    ]);

})(angular);
