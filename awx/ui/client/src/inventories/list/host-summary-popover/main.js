import directive from './host-summary-popover.directive';
import controller from './host-summary-popover.controller';

export default
angular.module('HostSummaryPopoverModule', [])
    .directive('hostSummaryPopover', directive)
    .controller('HostSummaryPopoverController', controller);
