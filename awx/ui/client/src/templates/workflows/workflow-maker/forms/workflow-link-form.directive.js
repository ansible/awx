/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowLinkFormController from './workflow-link-form.controller';

export default ['templateUrl',
    function(templateUrl) {
        return {
            scope: {
                linkConfig: '<',
                readOnly: '<',
                cancel: '&',
                select: '&',
                unlink: '&'
            },
            restrict: 'E',
            templateUrl: templateUrl('templates/workflows/workflow-maker/forms/workflow-link-form'),
            controller: workflowLinkFormController
        };
    }
];
