/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import promptOtherPrompts from './prompt-other-prompts.controller';

export default [ 'templateUrl',
    (templateUrl) => {
    return {
        scope: {
            promptData: '=',
            otherPromptsForm: '=',
            isActiveStep: '=',
            validate: '=',
            readOnlyPrompts: '<'
        },
        templateUrl: templateUrl('templates/prompt/steps/other-prompts/prompt-other-prompts'),
        controller: promptOtherPrompts,
        controllerAs: 'vm',
        require: ['^^prompt', 'promptOtherPrompts'],
        restrict: 'E',
        replace: true,
        transclude: true,
        link: (scope, el, attrs, controllers) => {

            const launchController = controllers[0];
            const promptOtherPromptsController = controllers[1];

            promptOtherPromptsController.init(scope, launchController, el);
        }
    };
}];
