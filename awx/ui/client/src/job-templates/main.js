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
import labels from './labels/main';

export default
angular.module('jobTemplates', [surveyMaker.name, jobTemplatesList.name, jobTemplatesAdd.name,
        jobTemplatesEdit.name, jobTemplatesCopy.name, labels.name
    ])
    .service('deleteJobTemplate', deleteJobTemplate)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();

            $stateProvider.state({
                name: 'jobTemplates',
                url: '/job_templates',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'jobTemplates',
                    modes: ['add', 'edit'],
                    list: 'JobTemplateList',
                    form: 'JobTemplateForm',
                    controllers: {
                        list: 'JobTemplatesList',
                        add: 'JobTemplatesAdd',
                        edit: 'JobTemplatesEdit'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'job_template',
                        socket: {
                            "groups": {
                                "jobs": ["status_changed"]
                            }
                        }
                    },
                })
            });
        }
    ]);
