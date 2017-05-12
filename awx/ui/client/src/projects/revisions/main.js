/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import revisions from './revisions.directive';

export default
    angular.module('revisions', [])
        .directive('revisions', revisions);