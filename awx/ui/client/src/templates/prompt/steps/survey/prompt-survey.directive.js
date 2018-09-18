/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import promptSurvey from './prompt-survey.controller';

export default [ 'templateUrl',
    (templateUrl) => {
    return {
        scope: {
            promptData: '=',
            surveyForm: '=',
            readOnlyPrompts: '<'
        },
        templateUrl: templateUrl('templates/prompt/steps/survey/prompt-survey'),
        controller: promptSurvey,
        controllerAs: 'vm',
        require: ['^^prompt', 'promptSurvey'],
        restrict: 'E',
        replace: true,
        transclude: true,
        link: (scope, el, attrs, controllers) => {

            const launchController = controllers[0];
            const promptSurveyController = controllers[1];

            promptSurveyController.init(scope, launchController);
        }
    };
}];
