/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import organizationsList from './list/main';
import organizationsAdd from './add/main';
import organizationsEdit from './edit/main';

export default
angular.module('organizations', [
    organizationsList.name,
    organizationsAdd.name,
    organizationsEdit.name,
]);
