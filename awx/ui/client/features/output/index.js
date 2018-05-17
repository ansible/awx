import atLibModels from '~models';
import atLibComponents from '~components';

import Strings from '~features/output/jobs.strings';
import Controller from '~features/output/index.controller';
import PageService from '~features/output/page.service';
import RenderService from '~features/output/render.service';
import ScrollService from '~features/output/scroll.service';
import EngineService from '~features/output/engine.service';
import StatusService from '~features/output/status.service';
import MessageService from '~features/output/message.service';
import EventsApiService from '~features/output/api.events.service';
import LegacyRedirect from '~features/output/legacy.route';

import DetailsComponent from '~features/output/details.component';
import SearchComponent from '~features/output/search.component';
import StatsComponent from '~features/output/stats.component';
import HostEvent from './host-event/index';

const Template = require('~features/output/index.view.html');

const MODULE_NAME = 'at.features.output';

const PAGE_CACHE = true;
const PAGE_LIMIT = 5;
const PAGE_SIZE = 50;
const WS_PREFIX = 'ws';

function resolveResource (
    $state,
    Job,
    ProjectUpdate,
    AdHocCommand,
    SystemJob,
    WorkflowJob,
    InventoryUpdate,
    $stateParams,
    qs,
    Wait,
    eventsApi,
) {
    const { id, type, handleErrors } = $stateParams;
    const { job_event_search } = $stateParams; // eslint-disable-line camelcase

    const { name, key } = getWebSocketResource(type);

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
        case 'inventory':
            Resource = InventoryUpdate;
            break;
        // case 'workflow':
            // todo: integrate workflow chart components into this view
            // break;
        default:
            // Redirect
            return null;
    }

    const params = {
        page_size: PAGE_SIZE,
        order_by: 'start_line',
    };

    const config = {
        params,
        pageCache: PAGE_CACHE,
        pageLimit: PAGE_LIMIT,
    };

    if (job_event_search) { // eslint-disable-line camelcase
        const query = qs.encodeQuerysetObject(qs.decodeArr(job_event_search));
        Object.assign(config.params, query);
    }

    let model;

    Wait('start');
    const resourcePromise = new Resource(['get', 'options'], [id, id])
        .then(job => {
            const endpoint = `${job.get('url')}${related}/`;
            eventsApi.init(endpoint, config.params);

            const promises = [job.getStats(), eventsApi.fetch()];

            if (job.has('related.labels')) {
                promises.push(job.extend('get', 'labels'));
            }

            model = job;
            return Promise.all(promises);
        })
        .then(([stats, events]) => ({
            id,
            type,
            stats,
            model,
            events,
            related,
            ws: {
                events: `${WS_PREFIX}-${key}-${id}`,
                status: `${WS_PREFIX}-${name}`,
            },
            page: {
                cache: PAGE_CACHE,
                size: PAGE_SIZE,
                pageLimit: PAGE_LIMIT
            }
        }));

    if (!handleErrors) {
        return resourcePromise
            .finally(() => Wait('stop'));
    }

    return resourcePromise
        .catch(({ data, status }) => {
            qs.error(data, status);
            return $state.go($state.current, $state.params, { reload: true });
        })
        .finally(() => Wait('stop'));
}

function resolveWebSocketConnection ($stateParams, SocketService) {
    const { type, id } = $stateParams;
    const { name, key } = getWebSocketResource(type);

    const state = {
        data: {
            socket: {
                groups: {
                    [name]: ['status_changed', 'summary'],
                    [key]: []
                }
            }
        }
    };

    return SocketService.addStateResolve(state, id);
}

function getWebSocketResource (type) {
    let name;
    let key;

    switch (type) {
        case 'system':
            name = 'jobs';
            key = 'system_job_events';
            break;
        case 'project':
            name = 'jobs';
            key = 'project_update_events';
            break;
        case 'command':
            name = 'jobs';
            key = 'ad_hoc_command_events';
            break;
        case 'inventory':
            name = 'jobs';
            key = 'inventory_update_events';
            break;
        case 'playbook':
            name = 'jobs';
            key = 'job_events';
            break;
        default:
            throw new Error('Unsupported WebSocket type');
    }

    return { name, key };
}

function JobsRun ($stateRegistry, strings) {
    const parent = 'jobs';
    const ncyBreadcrumb = { parent, label: strings.get('state.BREADCRUMB_DEFAULT') };

    const state = {
        url: '/:type/:id?job_event_search',
        name: 'output',
        parent,
        ncyBreadcrumb,
        params: {
            handleErrors: true,
        },
        data: {
            activityStream: false,
        },
        views: {
            '@': {
                templateUrl: Template,
                controller: Controller,
                controllerAs: 'vm'
            },
        },
        resolve: {
            webSocketConnection: [
                '$stateParams',
                'SocketService',
                resolveWebSocketConnection
            ],
            resource: [
                '$state',
                'JobModel',
                'ProjectUpdateModel',
                'AdHocCommandModel',
                'SystemJobModel',
                'WorkflowJobModel',
                'InventoryUpdateModel',
                '$stateParams',
                'QuerySet',
                'Wait',
                'JobEventsApiService',
                resolveResource
            ],
            breadcrumbLabel: [
                'resource',
                ({ model }) => {
                    ncyBreadcrumb.label = `${model.get('id')} - ${model.get('name')}`;
                }
            ],
        },
    };

    $stateRegistry.register(state);
}

JobsRun.$inject = ['$stateRegistry', 'JobStrings'];

angular
    .module(MODULE_NAME, [
        atLibModels,
        atLibComponents,
        HostEvent
    ])
    .service('JobStrings', Strings)
    .service('JobPageService', PageService)
    .service('JobScrollService', ScrollService)
    .service('JobRenderService', RenderService)
    .service('JobEventEngine', EngineService)
    .service('JobStatusService', StatusService)
    .service('JobMessageService', MessageService)
    .service('JobEventsApiService', EventsApiService)
    .component('atJobSearch', SearchComponent)
    .component('atJobStats', StatsComponent)
    .component('atJobDetails', DetailsComponent)
    .run(JobsRun)
    .run(LegacyRedirect);

export default MODULE_NAME;
