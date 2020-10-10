import galaxyCredentialsMultiselectController from './galaxy-credentials-multiselect.controller';
export default ['templateUrl', '$compile',
    function(templateUrl, $compile) {
        return {
            scope: {
                galaxyCredentials: '=',
                fieldIsDisabled: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('organizations/galaxy-credentials-multiselect/galaxy-credentials'),
            controller: galaxyCredentialsMultiselectController,
            link: function(scope) {
                scope.openInstanceGroupsModal = function() {
                    $('#content-container').append($compile('<galaxy-credentials-modal galaxy-credentials="galaxyCredentials"></galaxy-credentials-modal>')(scope));
                };
            }
        };
    }
];
