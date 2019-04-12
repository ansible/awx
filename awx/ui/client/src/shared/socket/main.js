/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import socketService from './socket.service';

export default
    angular.module('socket', [])
        .service('SocketService', socketService);
