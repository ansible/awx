import promptDirective from './prompt.directive';
import promptInventory from './steps/inventory/prompt-inventory.directive';
import promptCredential from './steps/credential/prompt-credential.directive';
import promptOtherPrompts from './steps/other-prompts/prompt-other-prompts.directive';
import promptSurvey from './steps/survey/prompt-survey.directive';
import promptPreview from './steps/preview/prompt-preview.directive';
import promptService from './prompt.service';

export default
    angular.module('prompt', [])
        .directive('prompt', promptDirective)
        .directive('promptInventory', promptInventory)
        .directive('promptCredential', promptCredential)
        .directive('promptOtherPrompts', promptOtherPrompts)
        .directive('promptSurvey', promptSurvey)
        .directive('promptPreview', promptPreview)
        .service('PromptService', promptService);
