export default
    [   '$scope',
        '$rootScope',
        'AboutAnsibleHelp',
        'ConfigureTower',
        function(
            $scope,
            $rootScope,
            showAboutModal,
            configureTower
        ) {
            $scope.showAboutModal = showAboutModal;

            $scope.showManagementJobsModal =
                configureTower.bind(null,
                                    {   scope: $rootScope,
                                        parent_scope: $rootScope
                                    });

        }
    ];
