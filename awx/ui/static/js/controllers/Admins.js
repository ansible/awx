/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Admins.js
 *
 *  Controller functions for ading Admins to an Organization.
 *
 */

'use strict';

function AdminsList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, AdminList, GenerateList, LoadBreadCrumbs,
    Prompt, SearchInit, PaginateInit, ReturnToCaller, GetBasePath, SelectionInit) {

    var list = AdminList,
        defaultUrl = GetBasePath('organizations') + $routeParams.organization_id + '/users/',
        generator = GenerateList,
        mode = 'select',
        url = GetBasePath('organizations') + $routeParams.organization_id + '/admins/';

    generator.inject(AdminList, { mode: mode, scope: $scope });

    SelectionInit({ scope: $scope, list: list, url: url, returnToCaller: 1 });

    SearchInit({ scope: $scope, set: 'admins', list: list, url: defaultUrl });

    PaginateInit({ scope: $scope, list: list, url: defaultUrl });

    $scope.search(list.iterator);

    LoadBreadCrumbs();
}

AdminsList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'AdminList', 'GenerateList',
    'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'GetBasePath', 'SelectionInit'
];