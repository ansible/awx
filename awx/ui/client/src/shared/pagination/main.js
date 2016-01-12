/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import pagination from './pagination.service';

export default
    angular.module('pagination', [])
        .factory('pagination', pagination);
