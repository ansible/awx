export default ['$rootScope', '$scope', '$location', 'ConfigService', 'lastPath',
    ($rootScope, $scope, $location, ConfigService, lastPath) => {

    ConfigService.getConfig()
        .then(function(config){
            $scope.version = config.version.split('-')[0];
            $scope.ansible_version = config.ansible_version;
            $scope.subscription = config.license_info.subscription_name;
            $scope.speechBubble = createSpeechBubble($rootScope.BRAND_NAME, config.version);
            $scope.currentYear = new Date().getFullYear();
            $('#about-modal').modal('show');
        });

    $('#about-modal').on('hidden.bs.modal', () => $location.url(lastPath));

    function createSpeechBubble (brand, version) {
        let text = `${brand} ${version}`;
        let top = '';
        let bottom = '';

        for (let i = 0; i < text.length; i++) {
            top += '_';
            bottom += '-';
        }

        top = ` __${top}__ \n`;
        text = `<  ${text}  >\n`;
        bottom = ` --${bottom}-- `;

        return top + text + bottom;
    }
}];
