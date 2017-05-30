import directive from './source-summary-popover.directive';
import controller from './source-summary-popover.controller';

export default
angular.module('SourceSummaryPopoverModule', [])
    .directive('sourceSummaryPopover', directive)
    .controller('SourceSummaryPopoverController', controller);
