/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import relatedHostAdd from './add/main';
 import relatedHostEdit from './edit/main';
 import relatedHostList from './list/main';
 import relatedHostsListDefinition from './related-host.list';
 import relatedHostsFormDefinition from './related-host.form';

export default
angular.module('relatedHost', [
        relatedHostAdd.name,
        relatedHostEdit.name,
        relatedHostList.name
    ])
    .factory('RelatedHostsFormDefinition', relatedHostsFormDefinition)
    .value('RelatedHostsListDefinition', relatedHostsListDefinition);
