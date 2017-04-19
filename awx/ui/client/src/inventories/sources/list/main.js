/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildSourcesListState from './build-sources-list-state.factory';
import controller from './sources-list.controller';

export default
    angular.module('sourcesList', [])
        .factory('buildSourcesListState', buildSourcesListState)
        .controller('SourcesListController', controller);
