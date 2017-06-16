import instanceGroupsMultiselectController from './instance-groups-multiselect.controller';
export default ['templateUrl', '$compile',
    function(templateUrl, $compile) {
        return {
            scope: {
                instanceGroups: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('instance-groups/instance-groups-multiselect/instance-groups'),
            controller: instanceGroupsMultiselectController,
            link: function(scope) {
                scope.openInstanceGroupsModal = function() {
                    $('#content-container').append($compile('<instance-groups-modal instance-groups="instanceGroups"></instance-groups-modal>')(scope));
                };
            }
        };
    }
];