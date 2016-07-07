/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ownerList from './ownerList.directive';

export default
    angular.module('credentials', [])
        .directive('ownerList', ownerList);
