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
    },
    ncyBreadcrumb: {
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
            templateProvider: function(ScheduleList, generateList){
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
        label: "{{breadcrumb.schedule_name}}"
    },
    resolve: editScheduleResolve()
};

// workflows
const workflowSchedulesRoute = {
    searchPrefix: 'schedule',
    name: 'templates.editWorkflowJobTemplate.schedules',
    route: '/schedules',
    data: {
        activityStream: true,
        activityStreamTarget: 'workflow_job_template',
    },
    ncyBreadcrumb: {
        label: N_('SCHEDULES')
    },
    resolve: {
        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('workflow_job_templates')}${$stateParams.workflow_job_template_id}/schedules`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath){
            let path = `${GetBasePath('workflow_job_templates')}${$stateParams.workflow_job_template_id}`;
            Rest.setUrl(path);
            return Rest.get(path).then(response => response.data);
        }],
        UnifiedJobsOptions: ['Rest', 'GetBasePath', '$stateParams', '$q',
            function(Rest, GetBasePath, $stateParams, $q) {
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
                list.basePath = GetBasePath('workflow_job_templates') + $stateParams.workflow_job_template_id + '/schedules/';
                return list;
            }
        ]
    },
    views: {
        related: {
            templateProvider: function(ScheduleList, generateList){
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

const workflowSchedulesAddRoute = {
    name: 'templates.editWorkflowJobTemplate.schedules.add',
    route: '/add',
    views: {
        'scheduler@templates': {
            controller: 'schedulerAddController',
            templateUrl: templateUrl("scheduler/schedulerForm"),
        }
    },
    ncyBreadcrumb: {
        label: N_('CREATE SCHEDULE')
    }
};

const workflowSchedulesEditRoute = {
    name: 'templates.editWorkflowJobTemplate.schedules.edit',
    route: '/:schedule_id',
    views: {
        'scheduler@templates': {
            controller: 'schedulerEditController',
            templateUrl: templateUrl("scheduler/schedulerForm"),
        }
    },
    ncyBreadcrumb: {
        label: '{{breadcrumb.schedule_name}}'
    },
    resolve: editScheduleResolve()
};

const projectsSchedulesListRoute = {
    searchPrefix: 'schedule',
    name: 'projects.edit.schedules',
    route: '/schedules',
    data: {
        activityStream: true,
        activityStreamTarget: 'project',
    },
    ncyBreadcrumb: {
        label: N_('SCHEDULES')
    },
    resolve: {
        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('projects')}${$stateParams.project_id}/schedules`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath){
            let path = `${GetBasePath('projects')}${$stateParams.project_id}`;
            Rest.setUrl(path);
            return Rest.get(path).then(response => response.data);
        }],
        UnifiedJobsOptions: ['Rest', 'GetBasePath', '$stateParams', '$q',
            function(Rest, GetBasePath, $stateParams, $q) {
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
                list.basePath = GetBasePath('projects') + $stateParams.project_id + '/schedules/';
                return list;
            }
        ]
    },
    views: {
        related: {
            templateProvider: function(ScheduleList, generateList){
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

const projectsSchedulesAddRoute = {
    name: 'projects.edit.schedules.add',
    route: '/add',
    ncyBreadcrumb: {
        label: N_('CREATE SCHEDULE')
    },
    views: {
        'scheduler@projects': {
            controller: 'schedulerAddController',
            templateUrl: templateUrl("scheduler/schedulerForm"),
        }
    }
};

const projectsSchedulesEditRoute = {
    name: 'projects.edit.schedules.edit',
    route: '/:schedule_id',
    ncyBreadcrumb: {
        label: "{{breadcrumb.schedule_name}}"
    },
    views: {
        'scheduler@projects': {
            controller: 'schedulerEditController',
            templateUrl: templateUrl("scheduler/schedulerForm"),
        }
    },
    resolve: editScheduleResolve()
};

const jobsSchedulesRoute = {
    searchPrefix: 'schedule',
    name: 'schedules',
    route: '/schedules',
    params: {
        schedule_search: {
            value: {
                order_by: 'unified_job_template__polymorphic_ctype__model'
            },
            dynamic: true
        }
    },
    data: {
        activityStream: false,
    },
    ncyBreadcrumb: {
        label: N_('SCHEDULES')
    },
    resolve: {
        ScheduleList: ['ScheduledJobsList', function(list){
            return list;
        }],
        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath('schedules');
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['GetBasePath', (GetBasePath) =>{return {endpoint:GetBasePath('schedules')}; }],
        UnifiedJobsOptions: ['Rest', 'GetBasePath', '$stateParams', '$q',
            function(Rest, GetBasePath, $stateParams, $q) {
                Rest.setUrl(GetBasePath('unified_jobs'));
                var val = $q.defer();
                Rest.options()
                    .then(function(data) {
                        val.resolve(data.data);
                    }, function(data) {
                        val.reject(data);
                    });
                return val.promise;
            }]
    },
    views: {
        '@': {
            templateProvider: function(ScheduleList, generateList){
                
                let html = generateList.build({
                    list: ScheduleList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                let formPlaceholder = generateList.insertFormView();
                html = formPlaceholder + html;
                return html;
            },
            controller: 'schedulerListController'
        }
    }
};

// the /#/jobs/schedules/:schedule_id state needs to know about the type of
// resource is being scheduled.
const parentResolve = {
    ParentObject: ['$stateParams', 'Rest', 'GetBasePath', 'scheduleResolve',
        function($stateParams, Rest, GetBasePath, scheduleResolve){
            let path = scheduleResolve.related.unified_job_template;
            Rest.setUrl(path);
            return Rest.get(path).then(response => response.data);
        }
    ]
};

const jobsSchedulesEditRoute = {
    name: 'schedules.edit',
    route: '/:schedule_id',
    ncyBreadcrumb: {
        parent: 'schedules',
        label: "{{breadcrumb.schedule_name}}"
    },
    views: {
        'form':{
            templateProvider: function(ParentObject, $http){
                let path;
                if(ParentObject.type === 'system_job_template'){
                    path = templateUrl('management-jobs/scheduler/schedulerForm');
                }
                else {
                    path = templateUrl('scheduler/schedulerForm');
                }
                return $http.get(path).then(response => response.data);
            },
            controllerProvider: function(ParentObject){
                if (ParentObject.type === 'system_job_template') {
                    return 'managementJobEditController';
                }
                else {
                    return 'schedulerEditController';
                }
            }
        }
    },
    resolve: _.merge(editScheduleResolve(), parentResolve)
};

export {
    jobTemplatesSchedulesListRoute,
    jobTemplatesSchedulesAddRoute,
    jobTemplatesSchedulesEditRoute,
    workflowSchedulesRoute,
    workflowSchedulesAddRoute,
    workflowSchedulesEditRoute,
    projectsSchedulesListRoute,
    projectsSchedulesAddRoute,
    projectsSchedulesEditRoute,
    jobsSchedulesRoute,
    jobsSchedulesEditRoute
};
