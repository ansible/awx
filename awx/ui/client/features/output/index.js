import JobsStrings from '~features/output/jobs.strings';
import IndexController from '~features/output/index.controller';
import atLibModels from '~models';
import atLibComponents from '~components';

import JobsStrings from '~features/output/jobs.strings';
import IndexController from '~features/output/index.controller';

const indexTemplate = require('~features/output/index.view.html');

const MODULE_NAME = 'at.features.output';
const PAGE_CACHE = true;
const PAGE_LIMIT = 3;
const PAGE_SIZE = 100;

function resolveResource (Job, ProjectUpdate, AdHocCommand, SystemJob, WorkflowJob, $stateParams) {
    const { id, type } = $stateParams;

    let Resource;
    let related = 'events';

    switch (type) {
        case 'project':
            Resource = ProjectUpdate;
            break;
        case 'playbook':
            Resource = Job;
            related = 'job_events';
            break;
        case 'command':
            Resource = AdHocCommand;
            break;
        case 'system':
            Resource = SystemJob;
            break;
        case 'workflow':
            Resource = WorkflowJob;
            break;
        default:
            // Redirect
            return null;
    }

    return new Resource('get', id)
        .then(model => model.extend(related, {
            pageCache: PAGE_CACHE,
            pageLimit: PAGE_LIMIT,
            params: {
                page_size: PAGE_SIZE,
                order_by: 'start_line'
            }
        }))
        .then(model => {
            return {
                id,
                type,
                model,
                related,
                ws: getWebSocketResource(type),
                page: {
                    cache: PAGE_CACHE,
                    limit: PAGE_LIMIT,
                    size: PAGE_SIZE
                }
            };
        });
}

function resolveWebSocket (SocketService, $stateParams) {
    const { type, id } = $stateParams;
    const prefix = 'ws';
    const resource = getWebSocketResource(type);

    let name;
    let events;

    const state = {
        data: {
            socket: {
                groups: {
                    [resource.name]: ['status_changed', 'summary'],
                    [resource.key]: []
                }
            }
        }
    };

    SocketService.addStateResolve(state, id);

    return `${prefix}-${resource.key}-${id}`;
}

function resolveBreadcrumb (strings) {
    return {
        label: strings.get('state.TITLE')
    };
}

function getWebSocketResource (type) {
    let name;
    let key;

    switch (type) {
        case 'system':
            name = 'system_jobs';
            key = 'system_job_events';
            break;
        case 'project':
            name = 'project_updates';
            key = 'project_update_events';
            break;
        case 'command':
            name = 'ad_hoc_commands';
            key = 'ad_hoc_command_events';
            break;
        case 'inventory':
            name = 'inventory_updates';
            key = 'inventory_update_events';
            break;
        case 'playbook':
            name = 'jobs';
            key = 'job_events';
            break;
    }

    return { name, key };
}


function JobsRun ($stateRegistry) {
    const state = {
        name: 'jobz',
        url: '/jobz/:type/:id',
        route: '/jobz/:type/:id',
        data: {
            activityStream: true,
            activityStreamTarget: 'jobs'
        },
        views: {
            '@': {
                templateUrl: indexTemplate,
                controller: IndexController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resource: [
                'JobModel',
                'ProjectUpdateModel',
                'AdHocCommandModel',
                'SystemJobModel',
                'WorkflowJobModel',
                '$stateParams',
                resolveResource
            ],
            ncyBreadcrumb: [
                'JobsStrings',
                resolveBreadcrumb
            ],
            webSocketNamespace: [
                'SocketService',
                '$stateParams',
                resolveWebSocket
            ]
        },
    };

    $stateRegistry.register(state);
}

JobsRun.$inject = ['$stateRegistry'];

angular
    .module(MODULE_NAME, [
        atLibModels,
        atLibComponents
    ])
    .controller('indexController', IndexController)
    .service('JobsStrings', JobsStrings)
    .run(JobsRun);

export default MODULE_NAME;
