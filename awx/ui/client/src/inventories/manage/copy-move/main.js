/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import CopyMoveGroupsController from './copy-move-groups.controller';
import CopyMoveHostsController from './copy-move-hosts.controller';
import CopyMoveGroupList from './copy-move-groups.list';

export default
angular.module('manageCopyMove', [])
    .controller('CopyMoveGroupsController', CopyMoveGroupsController)
    .controller('CopyMoveHostsController', CopyMoveHostsController)
    .value('CopyMoveGroupList', CopyMoveGroupList);
