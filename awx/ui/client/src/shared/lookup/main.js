/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import directive from './lookup-modal.directive';

export default
    angular.module('LookupModalModule', [])
        .directive('lookupModal', directive);
