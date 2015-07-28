/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import inventoryScriptsList from './list/main';
import inventoryScriptsAdd from './add/main';
import inventoryScriptsEdit from './edit/main';
import list from './inventory-scripts.list';
import form from './inventory-scripts.form';

export default
    angular.module('inventoryScripts', [
            inventoryScriptsList.name,
            inventoryScriptsAdd.name,
            inventoryScriptsEdit.name
        ])
        .factory('inventoryScriptsListObject', list)
        .factory('inventoryScriptsFormObject', form);
