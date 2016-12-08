/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowControls from './workflow-controls.directive';

export default
	angular.module('workflowControls', [])
		.directive('workflowControls', workflowControls);
