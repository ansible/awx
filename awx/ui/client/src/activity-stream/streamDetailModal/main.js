/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import streamDetailModalDirective from './streamDetailModal.directive';

export default
    angular.module('streamDetailModal', [])
        .directive('streamDetailModal', streamDetailModalDirective);
