/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import smartInventoryAdd from './add/main';
import smartInventoryEdit from './edit/main';
import smartInventoryForm from './smart-inventory.form';
import smartInventoryHostFilter from './smart-inventory-host-filter/smart-inventory-host-filter.directive';
import hostFilterModal from './smart-inventory-host-filter/host-filter-modal/host-filter-modal.directive';

export default
angular.module('smartInventory', [
        smartInventoryAdd.name,
        smartInventoryEdit.name
    ])
    .factory('smartInventoryForm', smartInventoryForm)
    .directive('smartInventoryHostFilter', smartInventoryHostFilter)
    .directive('hostFilterModal', hostFilterModal);
