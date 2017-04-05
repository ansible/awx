/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import hostAdd from './add/main';
 import hostEdit from './edit/main';
 import hostList from './list/main';
 import HostsNewList from './host.list';
 import HostsNewForm from './host.form';

export default
angular.module('hostnew', [
        hostAdd.name,
        hostEdit.name,
        hostList.name
    ])
    .factory('HostsNewForm', HostsNewForm)
    .factory('HostsNewList', HostsNewList);
