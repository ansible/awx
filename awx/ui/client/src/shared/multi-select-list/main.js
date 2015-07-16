/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import multiSelect from './multi-select-list.directive';
import selectAll from './select-all.directive';
import selectListItem from './select-list-item.directive';
import templateUrl from '../template-url/main';

export default
    angular.module('multiSelectList', [templateUrl.name])
        .directive('multiSelectList', multiSelect)
        .directive('selectAll', selectAll)
        .directive('selectListItem', selectListItem);
