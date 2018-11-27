/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowChart from './workflow-chart.directive';
import workflowChartService from './workflow-chart.service';

export default
	angular.module('workflowChart', [])
		.directive('workflowChart', workflowChart)
		.service('WorkflowChartService', workflowChartService);
