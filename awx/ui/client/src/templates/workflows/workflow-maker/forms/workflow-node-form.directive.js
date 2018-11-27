/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowNodeFormController from './workflow-node-form.controller';

export default ['templateUrl',
    function(templateUrl) {
        return {
            scope: {
                nodeConfig: '<',
                workflowJobTemplateObj: '<',
                cancel: '&',
                select: '&',
                readOnly: '<'
            },
            restrict: 'E',
            templateUrl: templateUrl('templates/workflows/workflow-maker/forms/workflow-node-form'),
            controller: workflowNodeFormController
        };
    }
];
