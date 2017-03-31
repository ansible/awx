/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import OrgAdminLookupFactory from './org-admin-lookup.factory';

export default
    angular.module('orgAdminLookup', [])
        .service('OrgAdminLookup', OrgAdminLookupFactory);
