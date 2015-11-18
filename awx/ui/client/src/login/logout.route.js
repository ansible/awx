/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'signOut',
    route: '/logout',
    controller: ['Authorization', '$location', function(Authorization, $location) {
        Authorization.logout();
        $location.path('/login');
    }],
    templateUrl: '/static/partials/blank.html'
};
