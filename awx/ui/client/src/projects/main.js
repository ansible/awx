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
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();
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
                                    msg: 'Failed to get credential tpyes. GET returned status: ' +
                                        response.status
                                });
                            });
                    }
                ]
            };
            // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
            // see: stateDefinition.factory for usage documentation
            $stateProvider.state({
                name: 'projects',
                url: '/projects',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'projects', // top-most node in the generated tree (will replace this state definition)
                    modes: ['add', 'edit'],
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
                    resolve: {
                        add: projectResolve,
                        edit: projectResolve
                    }
                })
            });
        }
    ]);
