/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ProjectsAdd from './add/projects-add.controller';
import ProjectsEdit from './edit/projects-edit.controller';
import ProjectsForm from './projects.form';
import GetProjectPath from './factories/get-project-path.factory';
import {
    projectsSchedulesListRoute,
    projectsSchedulesAddRoute,
    projectsSchedulesEditRoute
} from '../scheduler/schedules.route';

import ProjectsTemplatesRoute from '~features/templates/routes/projectsTemplatesList.route';
import projectsListRoute from '~features/projects/routes/projectsList.route.js';

export default
angular.module('Projects', [])
    .controller('ProjectsAdd', ProjectsAdd)
    .controller('ProjectsEdit', ProjectsEdit)
    .factory('GetProjectPath', GetProjectPath)
    .factory('ProjectsForm', ProjectsForm)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider,$stateExtenderProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();
            let stateExtender = $stateExtenderProvider.$get();

            function generateStateTree() {
                let projectAdd = stateDefinitions.generateTree({
                    name: 'projects.add',
                    url: '/add',
                    modes: ['add'],
                    form: 'ProjectsForm',
                    controllers: {
                        add: 'ProjectsAdd',
                    },
                });

                let projectEdit = stateDefinitions.generateTree({
                    name: 'projects.edit',
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
