/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import hostEdit from './edit/main';
 import hostList from './list/main';
 import HostsList from './host.list';
 import HostsForm from './host.form';
 import HostManageService from './hosts.service';
 import SetStatus from './set-status.factory';
 import SetEnabledMsg from './set-enabled-msg.factory';


export default
angular.module('host', [
        hostEdit.name,
        hostList.name
    ])
    .factory('HostsForm', HostsForm)
    .factory('HostsList', HostsList)
    .factory('SetStatus', SetStatus)
    .factory('SetEnabledMsg', SetEnabledMsg)
    .service('HostManageService', HostManageService);
