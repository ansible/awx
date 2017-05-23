import actionGroup from './action/action-group.directive';
import badge from './badge/badge.directive';
import dynamicInputGroup from './dynamic/input-group.directive';
import form from './form/form.directive';
import formAction from './form/action.directive';
import inputLabel from './input/label.directive';
import inputSearch from './input/search.directive';
import inputSelect from './input/select.directive';
import inputSecret from './input/secret.directive';
import inputText from './input/text.directive';
import inputTextarea from './input/textarea.directive';
import panel from './panel/panel.directive';
import panelHeading from './panel/heading.directive';
import panelBody from './panel/body.directive';
import popover from './popover/popover.directive';
import toggleButton from './toggle/button.directive';
import toggleContent from './toggle/content.directive';

import BaseInputController from './input/base.controller';

angular
    .module('at.lib.components', [])
    .directive('atActionGroup', actionGroup)
    .directive('atBadge', badge)
    .directive('atDynamicInputGroup', dynamicInputGroup)
    .directive('atForm', form)
    .directive('atFormAction', formAction)
    .directive('atInputLabel', inputLabel)
    .directive('atInputSearch', inputSearch)
    .directive('atInputSecret', inputSecret)
    .directive('atInputSelect', inputSelect)
    .directive('atInputText', inputText)
    .directive('atInputTextarea', inputTextarea)
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading)
    .directive('atPanelBody', panelBody)
    .directive('atPopover', popover)
    .directive('atToggleButton', toggleButton)
    .directive('atToggleContent', toggleContent)
    .service('BaseInputController', BaseInputController);


