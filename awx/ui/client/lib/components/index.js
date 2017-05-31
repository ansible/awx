import actionGroup from './action/action-group.directive';
import form from './form/form.directive';
import formAction from './form/action.directive';
import inputGroup from './input/group.directive';
import inputLabel from './input/label.directive';
import inputMessage from './input/message.directive';
import inputNumber from './input/number.directive';
import inputSelect from './input/select.directive';
import inputSecret from './input/secret.directive';
import inputText from './input/text.directive';
import inputTextarea from './input/textarea.directive';
import inputTextareaSecret from './input/textarea-secret.directive';
import panel from './panel/panel.directive';
import panelHeading from './panel/heading.directive';
import panelBody from './panel/body.directive';
import popover from './popover/popover.directive';
import tab from './tabs/tab.directive';
import tabGroup from './tabs/group.directive';

import BaseInputController from './input/base.controller';

angular
    .module('at.lib.components', [])
    .directive('atActionGroup', actionGroup)
    .directive('atForm', form)
    .directive('atFormAction', formAction)
    .directive('atInputGroup', inputGroup)
    .directive('atInputLabel', inputLabel)
    .directive('atInputMessage', inputMessage)
    .directive('atInputNumber', inputNumber)
    .directive('atInputSecret', inputSecret)
    .directive('atInputSelect', inputSelect)
    .directive('atInputText', inputText)
    .directive('atInputTextarea', inputTextarea)
    .directive('atInputTextareaSecret', inputTextareaSecret)
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading)
    .directive('atPanelBody', panelBody)
    .directive('atPopover', popover)
    .directive('atTab', tab)
    .directive('atTabGroup', tabGroup)
    .service('BaseInputController', BaseInputController);


