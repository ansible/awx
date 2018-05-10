import { N_ } from '../i18n';
import {templateUrl} from '../shared/template-url/template-url.factory';
import editScheduleResolve from './editSchedule.resolve';

const jobTemplatesSchedulesListRoute = {
    searchPrefix: 'schedule',
    name: 'templates.editJobTemplate.schedules',
    route: '/schedules',
    data: {
        activityStream: true,
        activityStreamTarget: 'job_template',
        activityStreamId: 'id'
    },
    ncyBreadcrumb: {
        parent: 'templates.editJobTemplate({job_template_id: parentObject.id})',
        label: N_('SCHEDULES')
    },
    resolve: {
        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('job_templates')}${$stateParams.job_template_id}/schedules`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath){
            let path = `${GetBasePath('job_templates')}${$stateParams.job_template_id}`;
            Rest.setUrl(path);
            return Rest.get(path).then(response => response.data);
        }],
        UnifiedJobsOptions: ['Rest', 'GetBasePath', '$q',
            function(Rest, GetBasePath, $q) {
                Rest.setUrl(GetBasePath('unified_jobs'));
                var val = $q.defer();
                Rest.options()
                    .then(function(data) {
                        val.resolve(data.data);
                    }, function(data) {
                        val.reject(data);
                    });
                return val.promise;
            }],
        ScheduleList: ['SchedulesList', 'GetBasePath', '$stateParams',
            (SchedulesList, GetBasePath, $stateParams) => {
                let list = _.cloneDeep(SchedulesList);
                list.basePath = GetBasePath('job_templates') + $stateParams.job_template_id + '/schedules/';
                return list;
            }
        ]
    },
    views: {
        related: {
            templateProvider: function(ScheduleList, generateList, ParentObject, $filter){
                ScheduleList.title = false;
                let html = generateList.build({
                    list: ScheduleList,
                    mode: 'edit'
                });
                return html;
            },
            controller: 'schedulerListController'
        }
    }
};

const jobTemplatesSchedulesAddRoute = {
    name: 'templates.editJobTemplate.schedules.add',
    route: '/add',
    views: {
        'scheduler@templates': {
            controller: 'schedulerAddController',
            templateUrl: templateUrl("scheduler/schedulerForm"),
        }
    },
    ncyBreadcrumb: {
        parent: 'templates.editJobTemplate({job_template_id: parentObject.id})',
        label: N_('CREATE SCHEDULE')
    }
};

const jobTemplatesSchedulesEditRoute = {
    name: 'templates.editJobTemplate.schedules.edit',
    route: '/:schedule_id',
    views: {
        'scheduler@templates': {
            controller: 'schedulerEditController',
            templateUrl: templateUrl("scheduler/schedulerForm"),
        }
    },
    ncyBreadcrumb: {
        parent: 'templates.editJobTemplate({job_template_id: parentObject.id})',
        label: '{{schedule_obj.name}}'
    },
    resolve: editScheduleResolve()
};

export {
    jobTemplatesSchedulesListRoute,
    jobTemplatesSchedulesAddRoute,
    jobTemplatesSchedulesEditRoute
};
