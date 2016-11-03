/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowMakerController from './workflow-maker.controller';

export default [ 'templateUrl',
    function(templateUrl) {
        return {
            scope: {
                treeData: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('job-templates/workflow-maker/workflow-maker'),
            controller: workflowMakerController,
        };
    }
];
