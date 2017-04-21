import badge from './badge.directive';
import inputSearch from './input-search.directive';
import panel from './panel.directive';
import panelHeading from './panel-heading.directive';
import panelBody from './panel-body.directive';

angular
    .module('at.components', [])
    .directive('atBadge', badge)
    .directive('atInputSearch', inputSearch)
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading)
    .directive('atPanelBody', panelBody);

