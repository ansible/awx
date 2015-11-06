/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import footerDirective from './footer.directive';

export default
    angular.module('footer', [])
        .directive('towerFooter', footerDirective);
