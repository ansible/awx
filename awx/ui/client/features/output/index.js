import JobsStrings from '~features/output/jobs.strings';
import IndexController from '~features/output/index.controller';
import atLibModels from '~models';
import atLibComponents from '~components';

import JobsStrings from '~features/output/jobs.strings';
import IndexController from '~features/output/index.controller';

const indexTemplate = require('~features/output/index.view.html');

const MODULE_NAME = 'at.features.output';

function resolveJob (Job, ProjectUpdate, AdHocCommand, SystemJob, WorkflowJob, $stateParams) {
    const { id } = $stateParams;
    const { type } = $stateParams;

    let Resource;
    let related;

    switch (type) {
        case 'project':
            Resource = ProjectUpdate;
            related = 'events';
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
        .then(resource => resource.extend(related, {
            pageCache: true,
            pageLimit: 3,
            params: {
                page_size: 100,
                order_by: 'start_line'
            }
        }))
        .catch(err => {
            console.error(err);
        });
}

function JobsRun ($stateExtender, strings) {
    $stateExtender.addState({
        name: 'jobz',
        route: '/jobz/:type/:id',
        ncyBreadcrumb: {
            label: strings.get('state.TITLE')
        },
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
            job: [
                'JobModel',
                'ProjectUpdateModel',
                'AdHocCommandModel',
                'SystemJobModel',
                'WorkflowJobModel',
                '$stateParams',
                resolveJob
            ]
        }
    });
}

JobsRun.$inject = ['$stateExtender', 'JobsStrings'];

angular
    .module(MODULE_NAME, [
        atLibModels,
        atLibComponents
    ])
    .controller('indexController', IndexController)
    .service('JobsStrings', JobsStrings)
    .run(JobsRun);

export default MODULE_NAME;
