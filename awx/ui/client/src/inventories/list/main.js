/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './inventory-list.controller';
import hostSummaryPopover from './host-summary-popover/main';
import sourceSummaryPopover from './source-summary-popover/main';

export default
angular.module('InventoryList', [
        hostSummaryPopover.name,
        sourceSummaryPopover.name
    ])
    .controller('InventoryListController', controller);
