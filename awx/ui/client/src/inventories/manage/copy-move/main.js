/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import CopyMoveGroupsController from './copy-move-groups.controller';
import CopyMoveHostsController from './copy-move-hosts.controller';

export default
angular.module('manageCopyMove', [])
    .controller('CopyMoveGroupsController', CopyMoveGroupsController)
    .controller('CopyMoveHostsController', CopyMoveHostsController);
