/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildSourcesAddState from './build-sources-add-state.factory';
import controller from './sources-add.controller';

export default
angular.module('sourcesAdd', [])
    .factory('buildSourcesAddState', buildSourcesAddState)
    .controller('SourcesAddController', controller);
