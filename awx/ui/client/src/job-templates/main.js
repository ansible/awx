/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import deleteJobTemplate from './delete-job-template.service';

import surveyMaker from './survey-maker/main';
import jobTemplatesList from './list/main';
import jobTemplatesAdd from './add/main';
import jobTemplatesEdit from './edit/main';
import jobTemplatesCopy from './copy/main';

export default
    angular.module('jobTemplates', 
    	[surveyMaker.name, jobTemplatesList.name, jobTemplatesAdd.name, 
    	jobTemplatesEdit.name, jobTemplatesCopy.name])
        .service('deleteJobTemplate', deleteJobTemplate);
