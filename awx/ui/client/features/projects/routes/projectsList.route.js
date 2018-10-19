import { N_ } from '../../../src/i18n';
import projectsListController from '../projectsList.controller';
import indexController from '../index.controller';

const indexTemplate = require('~features/projects/index.view.html');
const projectsListTemplate = require('~features/projects/projectsList.view.html');

export default {
    searchPrefix: 'project',
    name: 'projects',
    route: '/projects',
    ncyBreadcrumb: {
        label: N_('PROJECTS')
    },
    data: {
        activityStream: true,
        activityStreamTarget: 'project',
        socket: {
            groups: {
                jobs: ['status_changed']
            }
        }
    },
    params: {
        project_search: {
            dynamic: true,
        }
    },
    views: {
        '@': {
            templateUrl: indexTemplate,
            controller: indexController,
            controllerAs: 'vm'
        },
        'projectsList@projects': {
            templateUrl: projectsListTemplate,
            controller: projectsListController,
            controllerAs: 'vm',
        }
    },
    resolve: {
        CredentialTypes: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors',
            (Rest, $stateParams, GetBasePath, ProcessErrors) => {
                const path = GetBasePath('credential_types');
                Rest.setUrl(path);
                return Rest.get()
                    .then((data) => data.data.results)
                    .catch((response) => {
                        ProcessErrors(null, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: `Failed to get credential types. GET returned status: ${response.status}`,
                        });
                    });
            }
        ],
        ConfigData: ['ConfigService', 'ProcessErrors',
            (ConfigService, ProcessErrors) => ConfigService
                .getConfig()
                .then(response => response)
                .catch(({ data, status }) => {
                    ProcessErrors(null, data, status, null, {
                        hdr: 'Error!',
                        msg: `Failed to get config. GET returned status: status: ${status}`,
                    });
                })],
        Dataset: [
            '$stateParams',
            'Wait',
            'GetBasePath',
            'QuerySet',
            ($stateParams, Wait, GetBasePath, qs) => {
                const searchParam = $stateParams.project_search;
                const searchPath = GetBasePath('projects');

                Wait('start');
                return qs.search(searchPath, searchParam)
                    .finally(() => Wait('stop'));
            }
        ],
        resolvedModels: [
            'ProjectModel',
            (Project) => {
                const models = [
                    new Project(['options']),
                ];
                return Promise.all(models);
            },
        ],
    }
};
