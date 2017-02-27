/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowChart from './workflow-chart.directive';

export default
	angular.module('workflowChart', [])
		.directive('workflowChart', workflowChart);
