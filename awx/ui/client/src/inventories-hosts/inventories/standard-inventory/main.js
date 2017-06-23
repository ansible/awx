/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import inventoryAdd from './add/main';
 import inventoryEdit from './edit/main';
 import InventoryForm from './inventory.form';

export default
angular.module('standardInventory', [
        inventoryAdd.name,
        inventoryEdit.name
    ])
    .factory('InventoryForm', InventoryForm);
