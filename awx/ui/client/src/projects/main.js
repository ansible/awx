/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ProjectsList from './list/projects-list.controller';
import ProjectsAdd from './add/projects-add.controller';
import ProjectsEdit from './edit/projects-edit.controller';
import ProjectList from './projects.list';
import ProjectsForm from './projects.form';
import { N_ } from '../i18n';
import GetProjectPath from './factories/get-project-path.factory';
import GetProjectIcon from './factories/get-project-icon.factory';
import GetProjectToolTip from './factories/get-project-tool-tip.factory';
import {
    projectsSchedulesListRoute,
    projectsSchedulesAddRoute,
    projectsSchedulesEditRoute
} from '../scheduler/schedules.route';

import ProjectsTemplatesRoute from '~features/templates/routes/projectsTemplatesList.route';
import ProjectsStrings from './projects.strings';

export default
angular.module('Projects', [])
    .controller('ProjectsList', ProjectsList)
    .controller('ProjectsAdd', ProjectsAdd)
    .controller('ProjectsEdit', ProjectsEdit)
    .factory('GetProjectPath', GetProjectPath)
    .factory('GetProjectIcon', GetProjectIcon)
    .factory('GetProjectToolTip', GetProjectToolTip)
    .factory('ProjectList', ProjectList)
    .factory('ProjectsForm', ProjectsForm)
    .service('ProjectsStrings', ProjectsStrings)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider,$stateExtenderProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();
            let stateExtender = $stateExtenderProvider.$get();
            var projectResolve = {
                CredentialTypes: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors',
                    (Rest, $stateParams, GetBasePath, ProcessErrors) => {
                        var path = GetBasePath('credential_types');
                        Rest.setUrl(path);
                        return Rest.get()
                            .then(function(data) {
                                return (data.data.results);
                            }).catch(function(response) {
                                ProcessErrors(null, response.data, response.status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to get credential types. GET returned status: ' +
                                        response.status
                                });
                            });
                    }
                ],
                ConfigData: ['ConfigService', 'ProcessErrors', (ConfigService, ProcessErrors) => {
                    return ConfigService.getConfig()
                        .then(response => response)
                        .catch(({data, status}) => {
                            ProcessErrors(null, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get config. GET returned status: ' +
                                    'status: ' + status
                            });
                        });
                }]
            };

            function generateStateTree() {
                let projectTree = stateDefinitions.generateTree({
                    parent: 'projects', // top-most node in the generated tree (will replace this state definition)
                    modes: ['add', 'edit'],
                    generateSchedulerView: true,
                    list: 'ProjectList',
                    form: 'ProjectsForm',
                    controllers: {
                        list: ProjectsList, // DI strings or objects
                        add: ProjectsAdd,
                        edit: ProjectsEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'project',
                        socket: {
                            "groups": {
                                "jobs": ["status_changed"]
                            }
                        }
                    },
                    ncyBreadcrumb: {
                        label: N_('PROJECTS')
                    },
                    breadcrumbs: {
                        edit: '{{breadcrumb.project_name}}'
                    },
                    resolve: {
                        add: projectResolve,
                        edit: projectResolve
                    }
                });

                return Promise.all([
                    projectTree
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
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
