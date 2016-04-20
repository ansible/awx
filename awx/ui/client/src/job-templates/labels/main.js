/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import labelsList from './labelsList.directive';

export default
    angular.module('labels', [])
        .directive('labelsList', labelsList);
