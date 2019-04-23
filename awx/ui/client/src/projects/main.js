/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ProjectsAdd from './add/projects-add.controller';
import ProjectsEdit from './edit/projects-edit.controller';
import ProjectsForm from './projects.form';
import ProjectList from './projects.list';
import GetProjectPath from './factories/get-project-path.factory';
import GetProjectIcon from './factories/get-project-icon.factory';
import GetProjectToolTip from './factories/get-project-tool-tip.factory';
import {
    projectsSchedulesListRoute,
    projectsSchedulesAddRoute,
    projectsSchedulesEditRoute
} from '../scheduler/schedules.route';

import ProjectsTemplatesRoute from '~features/templates/routes/projectsTemplatesList.route';
import projectsListRoute from '~features/projects/routes/projectsList.route.js';


function ResolveScmCredentialType (GetBasePath, Rest, ProcessErrors) {
    Rest.setUrl(GetBasePath('credential_types') + '?kind=scm');

    return Rest.get()
        .then(({ data }) => {
            return data.results[0].id;
        })
        .catch(({ data, status }) => {
            ProcessErrors(null, data, status, null, {
                hdr: 'Error!',
                msg: 'Failed to get credential type data: ' + status
            });
        });
}

function ResolveInsightsCredentialType (GetBasePath, Rest, ProcessErrors) {
    Rest.setUrl(GetBasePath('credential_types') + '?name=Insights');

    return Rest.get()
        .then(({ data }) => {
            return data.results[0].id;
        })
        .catch(({ data, status }) => {
            ProcessErrors(null, data, status, null, {
                hdr: 'Error!',
                msg: 'Failed to get credential type data: ' + status
            });
        });
}

ResolveScmCredentialType.$inject = ['GetBasePath', 'Rest', 'ProcessErrors'];
ResolveInsightsCredentialType.$inject = ['GetBasePath', 'Rest', 'ProcessErrors'];


export default
angular.module('Projects', [])
    .controller('ProjectsAdd', ProjectsAdd)
    .controller('ProjectsEdit', ProjectsEdit)
    .factory('GetProjectPath', GetProjectPath)
    .factory('GetProjectIcon', GetProjectIcon)
    .factory('GetProjectToolTip', GetProjectToolTip)
    .factory('ProjectsForm', ProjectsForm)
    .factory('ProjectList', ProjectList)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider,$stateExtenderProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();
            let stateExtender = $stateExtenderProvider.$get();

            const projectsAddName = 'projects.add';
            const projectsEditName = 'projects.edit';

            function generateStateTree() {
                let projectAdd = stateDefinitions.generateTree({
                    name: projectsAddName,
                    url: '/add',
                    modes: ['add'],
                    form: 'ProjectsForm',
                    controllers: {
                        add: 'ProjectsAdd',
                    },
                })
                .then(res => {
                    const stateIndex = res.states.findIndex(s => s.name === projectsAddName);

                    res.states[stateIndex].resolve.scmCredentialType = ResolveScmCredentialType;
                    res.states[stateIndex].resolve.insightsCredentialType = ResolveInsightsCredentialType;

                    return res;
                });

                let projectEdit = stateDefinitions.generateTree({
                    name: projectsEditName,
                    url: '/:project_id',
                    modes: ['edit'],
                    form: 'ProjectsForm',
                    controllers: {
                        edit: 'ProjectsEdit',
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'project',
                        activityStreamId: 'project_id'
                    },
                    breadcrumbs: { 
                        edit: '{{breadcrumb.project_name}}'
                    },
                    resolve: {
                        edit: {
                            isNotificationAdmin: ['Rest', 'ProcessErrors', 'GetBasePath', 'i18n',
                                function(Rest, ProcessErrors, GetBasePath, i18n) {
                                    Rest.setUrl(`${GetBasePath('organizations')}?role_level=notification_admin_role&page_size=1`);
                                    return Rest.get()
                                        .then(({data}) => {
                                            return data.count > 0;
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get organizations for which this user is a notification administrator. GET returned ') + status
                                            });
                                    });
                            }]
                        }
                    }
                })
                .then(res => {
                    const stateIndex = res.states.findIndex(s => s.name === projectsEditName);

                    res.states[stateIndex].resolve.scmCredentialType = ResolveScmCredentialType;
                    res.states[stateIndex].resolve.insightsCredentialType = ResolveInsightsCredentialType;

                    return res;
                });

                return Promise.all([
                    projectAdd,
                    projectEdit,
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(projectsListRoute),
                            stateExtender.buildDefinition(ProjectsTemplatesRoute),
                            stateExtender.buildDefinition(projectsSchedulesListRoute),
                            stateExtender.buildDefinition(projectsSchedulesAddRoute),
                            stateExtender.buildDefinition(projectsSchedulesEditRoute)
                        ])
                    };
                });
            }
            let stateTree = {
                name: 'projects.**',
                url: '/projects',
                lazyLoad: () => generateStateTree()
            };
            $stateProvider.state(stateTree);
        }
    ]);
