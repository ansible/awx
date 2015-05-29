/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import multiSelect from './multi-select-list.directive';
import selectAll from './select-all.directive';
import selectListItem from './select-list-item.directive';

export default
    angular.module('multiSelectList', [])
        .directive('multiSelectList', multiSelect)
        .directive('selectAll', selectAll)
        .directive('selectListItem', selectListItem);
