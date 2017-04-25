import badge from './badge/badge.directive';
import inputSearch from './input/search.directive';
import panel from './panel/panel.directive';
import panelHeading from './panel/heading.directive';
import panelBody from './panel/body.directive';
import toggleButton from './toggle/button.directive';
import toggleContent from './toggle/content.directive';

angular
    .module('at.components', [])
    .directive('atBadge', badge)
    .directive('atInputSearch', inputSearch)
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading)
    .directive('atPanelBody', panelBody)
    .directive('atToggleButton', toggleButton)
    .directive('atToggleContent', toggleContent);


