/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'signOut',
    route: '/logout',
    controller: ['Authorization', '$state', function(Authorization, $state) {
        Authorization.logout().then( () =>{
            $state.go('signIn');
        });

    }],
    ncyBreadcrumb: {
        skip: true
    },
    templateUrl: '/static/partials/blank.html'
};
