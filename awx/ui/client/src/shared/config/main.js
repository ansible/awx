/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ConfigService from './config.service';

export default
    angular.module('config', [])
        .service('ConfigService', ConfigService);
