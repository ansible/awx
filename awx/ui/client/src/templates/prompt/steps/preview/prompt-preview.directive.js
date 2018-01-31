/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import promptPreview from './prompt-preview.controller';

export default [ 'templateUrl',
    (templateUrl) => {
    return {
        scope: {
            promptData: '='
        },
        templateUrl: templateUrl('templates/prompt/steps/preview/prompt-preview'),
        controller: promptPreview,
        controllerAs: 'vm',
        require: ['^^prompt', 'promptPreview'],
        restrict: 'E',
        replace: true,
        transclude: true,
        link: (scope, el, attrs, controllers) => {

            const launchController = controllers[0];
            const promptPreviewController = controllers[1];

            promptPreviewController.init(scope, launchController);
        }
    };
}];
