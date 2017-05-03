import badge from './badge/badge.directive';
import form from './form/form.directive';
import inputDropdown from './input/dropdown.directive';
import inputSearch from './input/search.directive';
import inputSelect from './input/select.directive';
import inputText from './input/text.directive';
import panel from './panel/panel.directive';
import panelHeading from './panel/heading.directive';
import panelBody from './panel/body.directive';
import toggleButton from './toggle/button.directive';
import toggleContent from './toggle/content.directive';

angular
    .module('at.components', [])
    .directive('atBadge', badge)
    .directive('atForm', form)
    .directive('atInputDropdown', inputDropdown)
    .directive('atInputSearch', inputSearch)
    .directive('atInputSelect', inputSelect)
    .directive('atInputText', inputText)
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading)
    .directive('atPanelBody', panelBody)
    .directive('atToggleButton', toggleButton)
    .directive('atToggleContent', toggleContent);


