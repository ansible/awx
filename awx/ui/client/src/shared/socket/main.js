/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import awFeatureDirective from './features.directive';
import socketService from './socket.service';

export default
    angular.module('socket', [])
        // .directive('awFeature', awFeatureDirective)
        .service('SocketService', socketService);
