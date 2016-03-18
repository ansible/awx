/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function manageHostDirectiveController($q, $rootScope, $scope, $state,
    $stateParams, $compile, Rest, ProcessErrors,
    CreateDialog, GetBasePath, Wait, GenerateList, GroupList, SearchInit,
    PaginateInit, GetRootGroups) {

        var vm = this;

    };

export default ['$q', '$rootScope', '$scope', '$state', '$stateParams',
    'ScopePass', '$compile', 'Rest', 'ProcessErrors', 'CreateDialog',
    'GetBasePath', 'Wait', 'generateList', 'GroupList', 'SearchInit',
    'PaginateInit', 'GetRootGroups', manageHostDirectiveController
];
