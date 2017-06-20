/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './groups-list.controller';

export default
    angular.module('groupsList', [])
        .controller('GroupsListController', controller);
