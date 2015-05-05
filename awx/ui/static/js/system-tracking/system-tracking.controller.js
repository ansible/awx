function controller($rootScope, $scope, $routeParams, $location, $q, factDataServiceFactory, moment) {

    var service;
    var inventoryId = $routeParams.id;
    var hostIds = $routeParams.hosts.split(',');
    var moduleParam = $location.search().module || 'packages';

    var configReadyOff =
        $rootScope.$on('ConfigReady', function() {
            $(".date").systemTrackingDP({
                autoclose: true
            });
            configReadyOff();
        });

    $scope.leftFilterValue = hostIds[0];
    $scope.rightFilterValue = hostIds[1];

    $scope.factModulePickersLabelLeft = "Fact collection date for host " + $scope.leftFilterValue;
    $scope.factModulePickersLabelRight = "Fact collection date for host " + $scope.rightFilterValue;

    $scope.modules =
        [{  name: 'packages',
            displayName: 'Packages',
            isActive: true,
            displayType: 'flat'
         },
         {  name: 'services',
            displayName: 'Services',
            isActive: false,
            displayType: 'flat'
         },
         {  name: 'files',
            displayName: 'Files',
            isActive: false,
            displayType: 'flat'
         },
         {  name: 'ansible',
            displayName: 'Ansible',
            isActive: false,
            displayType: 'nested'
         }
        ];

    // Use this to determine how to orchestrate the services
    var viewType = hostIds.length > 1 ? 'multiHost' : 'singleHost';

    if (viewType === 'singleHost') {
        var startDate = moment();
        $scope.leftFilterValue = startDate;
        $scope.rightFilterValue = startDate.clone().subtract(1, 'days');
    }

    service = factDataServiceFactory(viewType);

    function reloadData(activeModule) {
        activeModule.then(function(module) {
            $scope.factData =
                service.get(inventoryId,
                            module.name,
                            $scope.leftFilterValue,
                            $scope.rightFilterValue);
        });
    }

    $scope.setActiveModule = function(newModuleName) {

        var newModule = _.find($scope.modules, function(module) {
            return module.name === newModuleName;
        });

        $scope.modules.forEach(function(module) {
            module.isActive = false;
        });

        newModule.isActive = true;
        $location.search('module', newModuleName);

        reloadData($q.when(newModule));

    };


    $scope.setActiveModule(moduleParam);
}

export default
    [   '$rootScope',
        '$scope',
        '$routeParams',
        '$location',
        '$q',
        'factDataServiceFactory',
        'moment',
        controller
    ];
