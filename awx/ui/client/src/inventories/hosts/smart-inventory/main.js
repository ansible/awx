/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import smartInventoryAdd from './add/main';
 import smartInventoryEdit from './edit/main';
 import SmartInventoryForm from './smart-inventory.form';
 import dynamicInventoryHostFilter from './dynamic-inventory-host-filter/dynamic-inventory-host-filter.directive';
 import hostFilterModal from './dynamic-inventory-host-filter/host-filter-modal/host-filter-modal.directive';

export default
angular.module('smartInventory', [
        smartInventoryAdd.name,
        smartInventoryEdit.name
    ])
    .factory('SmartInventoryForm', SmartInventoryForm)
    .directive('dynamicInventoryHostFilter', dynamicInventoryHostFilter)
    .directive('hostFilterModal', hostFilterModal);
