/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import detailsController from './details.controller';

const templateUrl = require('~network-ui/network-details/details.partial.html');

export default [
    function() {
    return {
        scope:{
            item: "=",
            canAdd: '@'
        },
        templateUrl,
        controller: detailsController,
        restrict: 'E',
    };
}];
