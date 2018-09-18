/* eslint camelcase: 0 */
import atLibModels from '~models';
import atLibComponents from '~components';

import Strings from '~features/output/output.strings';
import Controller from '~features/output/index.controller';
import RenderService from '~features/output/render.service';
import ScrollService from '~features/output/scroll.service';
import StreamService from '~features/output/stream.service';
import StatusService from '~features/output/status.service';
import MessageService from '~features/output/message.service';
import EventsApiService from '~features/output/api.events.service';
import PageService from '~features/output/page.service';
import SlideService from '~features/output/slide.service';
import LegacyRedirect from '~features/output/legacy.route';

import DetailsComponent from '~features/output/details.component';
import SearchComponent from '~features/output/search.component';
import StatsComponent from '~features/output/stats.component';
import HostEvent from './host-event/index';

import {
    API_ROOT,
    OUTPUT_ORDER_BY,
    OUTPUT_PAGE_SIZE,
    WS_PREFIX,
} from './constants';

const MODULE_NAME = 'at.features.output';
const Template = require('~features/output/index.view.html');

function resolveResource (
    $state,
    $stateParams,
    Job,
    ProjectUpdate,
    AdHocCommand,
    SystemJob,
    WorkflowJob,
    InventoryUpdate,
    qs,
    Wait,
    Events,
) {
    const { id, type, handleErrors, job_event_search } = $stateParams;
    const { name, key } = getWebSocketResource(type);

    let Resource;
    let related;

    switch (type) {
        case 'project':
            Resource = ProjectUpdate;
            related = `project_updates/${id}/events/`;
            break;
        case 'playbook':
            Resource = Job;
            related = `jobs/${id}/job_events/`;
            break;
        case 'command':
            Resource = AdHocCommand;
            related = `ad_hoc_commands/${id}/events/`;
            break;
        case 'system':
            Resource = SystemJob;
            related = `system_jobs/${id}/events/`;
            break;
        case 'inventory':
            Resource = InventoryUpdate;
            related = `inventory_updates/${id}/events/`;
            break;
        // case 'workflow':
            // todo: integrate workflow chart components into this view
            // break;
        default:
            // Redirect
            return null;
    }

    const params = {
        page_size: OUTPUT_PAGE_SIZE,
        order_by: OUTPUT_ORDER_BY,
    };

    if (job_event_search) {
        const query = qs.encodeQuerysetObject(qs.decodeArr(job_event_search));
        Object.assign(params, query);
    }

    Events.init(`${API_ROOT}${related}`, params);

    Wait('start');
    const promise = Promise.all([new Resource(['get', 'options'], [id, id]), Events.fetch()])
        .then(([model, events]) => ({
            id,
            type,
            model,
            events,
            ws: {
                events: `${WS_PREFIX}-${key}-${id}`,
                status: `${WS_PREFIX}-${name}`,
                summary: `${WS_PREFIX}-${name}-summary`,
            },
        }));

    if (!handleErrors) {
        return promise
            .finally(() => Wait('stop'));
    }

    return promise
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

    SocketService.addStateResolve(state, id);
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

function JobsRun ($stateRegistry, $filter, strings) {
    const parent = 'jobs';
    const ncyBreadcrumb = { parent, label: strings.get('state.BREADCRUMB_DEFAULT') };
    const sanitize = $filter('sanitize');

    const state = {
        url: '/:type/:id?job_event_search?_debug',
        name: 'output',
        parent,
        ncyBreadcrumb,
        params: {
            handleErrors: true,
            isPanelExpanded: false,
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
                '$stateParams',
                'JobModel',
                'ProjectUpdateModel',
                'AdHocCommandModel',
                'SystemJobModel',
                'WorkflowJobModel',
                'InventoryUpdateModel',
                'QuerySet',
                'Wait',
                'JobEventsApiService',
                resolveResource
            ],
            breadcrumbLabel: [
                'resource',
                ({ model }) => {
                    ncyBreadcrumb.label = `${model.get('id')} - ${sanitize(model.get('name'))}`;
                }
            ],
        },
    };

    $stateRegistry.register(state);
}

JobsRun.$inject = ['$stateRegistry', '$filter', 'OutputStrings'];

angular
    .module(MODULE_NAME, [
        atLibModels,
        atLibComponents,
        HostEvent
    ])
    .service('OutputStrings', Strings)
    .service('OutputScrollService', ScrollService)
    .service('OutputRenderService', RenderService)
    .service('OutputStreamService', StreamService)
    .service('OutputStatusService', StatusService)
    .service('OutputMessageService', MessageService)
    .service('JobEventsApiService', EventsApiService)
    .service('OutputPageService', PageService)
    .service('OutputSlideService', SlideService)
    .component('atJobSearch', SearchComponent)
    .component('atJobStats', StatsComponent)
    .component('atJobDetails', DetailsComponent)
    .run(JobsRun)
    .run(LegacyRedirect);

export default MODULE_NAME;
