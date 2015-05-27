export default
    [   '$scope',
        '$rootScope',
        'AboutAnsibleHelp',
        'LicenseViewer',
        'ConfigureTower',
        'CreateCustomInventory',
        function(
            $scope,
            $rootScope,
            showAboutModal,
            licenseViewer,
            configureTower,
            showInventoryScriptsModal
        ) {
            $scope.showAboutModal = showAboutModal;
            $scope.showLicenseModal = licenseViewer.showViewer.bind(licenseViewer);

            $scope.showManagementJobsModal =
                configureTower.bind(null,
                                    {   scope: $rootScope,
                                        parent_scope: $rootScope
                                    });

            $scope.showInventoryScriptsModal = showInventoryScriptsModal.bind(null,
                                                                              { parent_scope: $rootScope
                                                                              });

        }
    ]
