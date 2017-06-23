/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import hosts from './hosts/main';
 import inventories from './inventories/main';
 import shared from './shared/main';

export default
angular.module('inventories-hosts', [
        hosts.name,
        inventories.name,
        shared.name
    ]);
