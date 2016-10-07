/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import listGenerator from './list-generator/main';
import pagination from './pagination/main';
import lodashAsPromised from './lodash-as-promised';
import stringFilters from './string-filters/main';
import truncatedText from './truncated-text.directive';
import stateExtender from './stateExtender.provider';
import rbacUiControl from './rbacUiControl';
import socket from './socket/main';

export default
angular.module('shared', [listGenerator.name,
        pagination.name,
        stringFilters.name,
        'ui.router',
        rbacUiControl.name,
        socket.name
    ])
    .factory('lodashAsPromised', lodashAsPromised)
    .directive('truncatedText', truncatedText)
    .provider('$stateExtender', stateExtender);
