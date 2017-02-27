/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import directive from './paginate.directive';
import controller from './paginate.controller';

export default
    angular.module('PaginateModule', [])
        .directive('paginate', directive)
        .controller('PaginateController', controller);
