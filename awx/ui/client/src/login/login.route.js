/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'signIn',
    route: '/login',
    templateUrl: templateUrl('login/loginBackDrop'),
    controller: ['$rootScope', 'Authorization', function($rootScope, Authorization) {
        if (Authorization.isUserLoggedIn()) {
            Authorization.logout();
        }
        $(".LoginModal-dialog").remove();
    }],
    ncyBreadcrumb: {
        skip: true
    }

};
