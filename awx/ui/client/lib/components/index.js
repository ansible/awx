import action from './action/action.directive';
import actionGroup from './action/action-group.directive';
import badge from './badge/badge.directive';
import form from './form/form.directive';
import inputLabel from './input/label.directive';
import inputSearch from './input/search.directive';
import inputSelect from './input/select.directive';
import inputText from './input/text.directive';
import panel from './panel/panel.directive';
import panelHeading from './panel/heading.directive';
import panelBody from './panel/body.directive';
import popover from './popover/popover.directive';
import toggleButton from './toggle/button.directive';
import toggleContent from './toggle/content.directive';

angular
    .module('at.lib.components', [])
    .directive('atAction', action)
    .directive('atActionGroup', actionGroup)
    .directive('atBadge', badge)
    .directive('atForm', form)
    .directive('atInputLabel', inputLabel)
    .directive('atInputSearch', inputSearch)
    .directive('atInputSelect', inputSelect)
    .directive('atInputText', inputText)
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading)
    .directive('atPanelBody', panelBody)
    .directive('atPopover', popover)
    .directive('atToggleButton', toggleButton)
    .directive('atToggleContent', toggleContent);


