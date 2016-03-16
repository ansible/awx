/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import inventoryAdd from './add/main';
import inventoryEdit from './edit/main';
import inventoryList from './list/main';
import inventoryManage from './manage/main';

export default
angular.module('inventory', [
    inventoryAdd.name,
    inventoryEdit.name,
    inventoryList.name,
    inventoryManage.name,
]);
