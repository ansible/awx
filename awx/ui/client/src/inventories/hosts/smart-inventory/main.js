/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import smartInventoryAdd from './add/main';
 import smartInventoryEdit from './edit/main';
 import SmartInventoryForm from './smart-inventory.form';

export default
angular.module('smartInventory', [
        smartInventoryAdd.name,
        smartInventoryEdit.name
    ])
    .factory('SmartInventoryForm', SmartInventoryForm);
