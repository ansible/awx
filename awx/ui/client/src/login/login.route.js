/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'signIn',
    route: '/login',
    socket: null,
    templateUrl: templateUrl('login/loginBackDrop'),
    resolve: {
        obj: ['$rootScope', 'Authorization',
        function($rootScope, Authorization) {
            $rootScope.configReady = true;
            if (Authorization.isUserLoggedIn()) {
                Authorization.logout();
            }
            $(".LoginModal-dialog").remove();
        }]
    },
    ncyBreadcrumb: {
        skip: true
    }

};
