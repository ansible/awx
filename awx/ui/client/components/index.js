import panel from './panel.directive';
import panelHeading from './panel-heading.directive';

angular
    .module('at.components', [])
    .directive('atPanel', panel)
    .directive('atPanelHeading', panelHeading);

