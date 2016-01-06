/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import authentication from './authenticationServices/main';
import loginModal from './loginModal/main';

import loginRoute from './login.route';
import logoutRoute from './logout.route';

export default
    angular.module('login', [authentication.name, loginModal.name])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(loginRoute);
            $stateExtender.addState(logoutRoute);
        }]);
