/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import LaunchJob from './job-submission-factories/launchjob.factory';
import AdhocRun from './job-submission-factories/adhoc-run.factory.js';
import CheckPasswords from './job-submission-factories/check-passwords.factory';
import CreateLaunchDialog from './job-submission-factories/create-launch-dialog.factory';
import InventoryUpdate from './job-submission-factories/inventory-update.factory';
import ProjectUpdate from './job-submission-factories/project-update.factory';
import PromptForPasswords from './job-submission-factories/prompt-for-passwords.factory';
import awPasswordMin from './job-submission-directives/aw-password-min.directive';
import awPasswordMax from './job-submission-directives/aw-password-max.directive';

export default
	angular.module('jobSubmission', [])
		.factory('LaunchJob', LaunchJob)
		.factory('AdhocRun', AdhocRun)
		.factory('CheckPasswords', CheckPasswords)
		.factory('CreateLaunchDialog', CreateLaunchDialog)
		.factory('InventoryUpdate', InventoryUpdate)
		.factory('ProjectUpdate', ProjectUpdate)
		.factory('PromptForPasswords', PromptForPasswords)
		.directive('awPasswordMin', awPasswordMin)
		.directive('awPasswordMax', awPasswordMax);
