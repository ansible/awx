/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import InitiatePlaybookRun from './job-submission-factories/initiateplaybookrun.factory';
import LaunchJob from './job-submission-factories/launchjob.factory';
import GetSurveyQuestions from './job-submission-factories/getsurveyquestions.factory';
import submitJob from './job-submission.directive';
import credentialList from './lists/credential/job-sub-cred-list.directive';
import inventoryList from './lists/inventory/job-sub-inv-list.directive';
import awPasswordMin from './job-submission-directives/aw-password-min.directive';
import awPasswordMax from './job-submission-directives/aw-password-max.directive';

export default
	angular.module('jobSubmission', [])
		.factory('InitiatePlaybookRun', InitiatePlaybookRun)
		.factory('LaunchJob', LaunchJob)
		.factory('GetSurveyQuestions', GetSurveyQuestions)
		.directive('submitJob', submitJob)
		.directive('jobSubCredList', credentialList)
		.directive('jobSubInvList', inventoryList)
		.directive('awPasswordMin', awPasswordMin)
		.directive('awPasswordMax', awPasswordMax);
