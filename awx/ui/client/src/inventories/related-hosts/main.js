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
 import relatedGroupsLabels from './related-groups-labels/main';

export default
angular.module('relatedHost', [
        relatedHostAdd.name,
        relatedHostEdit.name,
        relatedHostList.name,
        relatedGroupsLabels.name
    ])
    .factory('RelatedHostsFormDefinition', relatedHostsFormDefinition)
    .factory('RelatedHostsListDefinition', relatedHostsListDefinition);
