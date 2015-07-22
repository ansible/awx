export default
    [   '$scope',
        '$rootScope',
        'AboutAnsibleHelp',
        function(
            $scope,
            $rootScope,
            showAboutModal
        ) {
            $scope.showAboutModal = showAboutModal;
        }
    ];
