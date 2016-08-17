/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import listGenerator from './list-generator/main';
import pagination from './pagination/main';
import title from './title.directive';
import lodashAsPromised from './lodash-as-promised';
import stringFilters from './string-filters/main';
import truncatedText from './truncated-text.directive';
import stateExtender from './stateExtender.provider';

export default
angular.module('shared', [listGenerator.name,
        pagination.name,
        stringFilters.name,
        'ui.router'
    ])
    .factory('lodashAsPromised', lodashAsPromised)
    .directive('truncatedText', truncatedText)
    //.directive('title', title)
    .provider('$stateExtender', stateExtender);
