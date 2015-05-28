export default
    [   '$scope',
        '$rootScope',
        'AboutAnsibleHelp',
        'ConfigureTower',
        'CreateCustomInventory',
        function(
            $scope,
            $rootScope,
            showAboutModal,
            configureTower,
            showInventoryScriptsModal
        ) {
            $scope.showAboutModal = showAboutModal;

            $scope.showManagementJobsModal =
                configureTower.bind(null,
                                    {   scope: $rootScope,
                                        parent_scope: $rootScope
                                    });

            $scope.showInventoryScriptsModal = showInventoryScriptsModal.bind(null,
                                                                              { parent_scope: $rootScope
                                                                              });

        }
    ];
