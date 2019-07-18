/*************************************************
 * Copyright (c) 2019 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowKey from './workflow-key.directive';

export default
	angular.module('workflowKey', [])
		.directive('workflowKey', workflowKey);
