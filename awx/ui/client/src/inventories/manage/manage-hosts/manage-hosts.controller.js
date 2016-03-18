/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function manageHostDirectiveController($q, $rootScope, $scope, $state,
    $stateParams, $compile, ScopePass, Rest, ProcessErrors,
    CreateDialog, GetBasePath, Wait, GenerateList, GroupList, SearchInit,
    PaginateInit, GetRootGroups) {

    var vm = this;
    console.info(ScopePass);

};

export default ['$q', '$rootScope', '$scope', '$state', '$stateParams',
    'ScopePass', '$compile', 'ScopePass', 'Rest', 'ProcessErrors', 'CreateDialog',
    'GetBasePath', 'Wait', 'generateList', 'GroupList', 'SearchInit',
    'PaginateInit', 'GetRootGroups',
    manageHostDirectiveController
];
