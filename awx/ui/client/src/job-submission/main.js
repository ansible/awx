/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import InitiatePlaybookRun from './job-submission-factories/initiateplaybookrun.factory';
import LaunchJob from './job-submission-factories/launchjob.factory';
import GetSurveyQuestions from './job-submission-factories/getsurveyquestions.factory';
import submitJob from './job-submission.directive';

export default
	angular.module('jobSubmission', [])
		.factory('InitiatePlaybookRun', InitiatePlaybookRun)
		.factory('LaunchJob', LaunchJob)
		.factory('GetSurveyQuestions', GetSurveyQuestions)
		.directive('submitJob', submitJob);
