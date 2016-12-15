/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {templateUrl} from '../../../shared/template-url/template-url.factory';

import CopyMoveGroupsController from './copy-move-groups.controller';
import CopyMoveHostsController from './copy-move-hosts.controller';

var copyMoveGroupRoute = {
    name: 'inventoryManage.copyMoveGroup',
    url: '/copy-move-group/{group_id:int}',
    searchPrefix: 'copy',
    data: {
        group_id: 'group_id',
    },
    params: {
        copy_search: {
            value: {
                not__id__in: null
            },
            dynamic: true,
            squash: ''
        }
    },
    ncyBreadcrumb: {
        label: "COPY OR MOVE {{item.name}}"
    },
    resolve: {
        Dataset: ['CopyMoveGroupList', 'QuerySet', '$stateParams', 'GetBasePath', 'group',
            function(list, qs, $stateParams, GetBasePath, group) {
                $stateParams.copy_search.not__id__in = ($stateParams.group.length > 0 ? group.id + ',' + _.last($stateParams.group) : group.id);
                let path = GetBasePath(list.name);
                return qs.search(path, $stateParams.copy_search);
            }
        ],
        group: ['GroupManageService', '$stateParams', function(GroupManageService, $stateParams){
            return GroupManageService.get({id: $stateParams.group_id}).then(res => res.data.results[0]);
        }]
    },
    views: {
        'form@inventoryManage' : {
            controller: CopyMoveGroupsController,
            templateUrl: templateUrl('inventories/manage/copy-move/copy-move'),
        },
        'copyMoveList@inventoryManage.copyMoveGroup': {
            templateProvider: function(CopyMoveGroupList, generateList) {
                let html = generateList.build({
                    list: CopyMoveGroupList,
                    mode: 'lookup',
                    input_type: 'radio'
                });
                return html;
            }
        }
    }
};
var copyMoveHostRoute = {
    name: 'inventoryManage.copyMoveHost',
    url: '/copy-move-host/{host_id}',
    searchPrefix: 'copy',
    ncyBreadcrumb: {
        label: "COPY OR MOVE {{item.name}}"
    },
    resolve: {
        Dataset: ['CopyMoveGroupList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.name);
                return qs.search(path, $stateParams.copy_search);
            }
        ],
        host: ['HostManageService', '$stateParams', function(HostManageService, $stateParams){
            return HostManageService.get({id: $stateParams.host_id}).then(res => res.data.results[0]);
        }]
    },
    views: {
        'form@inventoryManage': {
            templateUrl: templateUrl('inventories/manage/copy-move/copy-move'),
            controller: CopyMoveHostsController,
        },
        'copyMoveList@inventoryManage.copyMoveHost': {
            templateProvider: function(CopyMoveGroupList, generateList) {
                let html = generateList.build({
                    list: CopyMoveGroupList,
                    mode: 'lookup',
                    input_type: 'radio'
                });
                return html;
            }
        }
    }
};

export {copyMoveGroupRoute, copyMoveHostRoute};
