/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import authenticationService from './authentication.service';
import isAdmin from './isAdmin.factory';
import timer from './timer.factory';
import pendoService from './pendo.service';
import insightsEnablementService from './insightsEnablement.service';

export default
    angular.module('authentication', [])
        .factory('Authorization', authenticationService)
        .factory('IsAdmin', isAdmin)
        .factory('Timer', timer)
        .service('pendoService', pendoService)
        .service('insightsEnablementService', insightsEnablementService);
