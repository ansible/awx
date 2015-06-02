/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import listGenerator from './list-generator/main';
import title from './title.directive';
import lodashAsPromised from './lodash-as-promised';
import stringFilters from './string-filters/main';

export default
    angular.module('shared',
                   [    listGenerator.name,
                        stringFilters.name
                   ])
        .factory('lodashAsPromised', lodashAsPromised)
        .directive('title', title);
