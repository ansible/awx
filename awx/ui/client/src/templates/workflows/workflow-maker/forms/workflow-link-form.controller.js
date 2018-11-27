/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'TemplatesStrings', 'CreateSelect2',
    function($scope, TemplatesStrings, CreateSelect2) {
        $scope.strings = TemplatesStrings;

        $scope.edgeTypeOptions = [
            {
                label: $scope.strings.get('workflow_maker.ALWAYS'),
                value: 'always'
            },
            {
                label: $scope.strings.get('workflow_maker.ON_SUCCESS'),
                value: 'success'
            },
            {
                label: $scope.strings.get('workflow_maker.ON_FAILURE'),
                value: 'failure'
            }
        ];

        $scope.$watch('linkConfig.edgeType', () => {
            if (_.has($scope, 'linkConfig.edgeType')) {
                $scope.edgeType = {
                    value: $scope.linkConfig.edgeType
                };
                CreateSelect2({
                    element: '#workflow_link_edge',
                    multiple: false
                });
            }
        });
    }
];
