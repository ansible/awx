/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import listGenerator from './list-generator/main';
import title from './title.directive';
import lodashAsPromised from './lodash-as-promised';

export default
    angular.module('shared', [listGenerator.name])
        .factory('lodashAsPromised', lodashAsPromised)
        .directive('title', title);
