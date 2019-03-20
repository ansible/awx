
import AddController from './add-applications.controller';
import EditController from './edit-applications.controller';
import ListController from './list-applications.controller';
import UserListController from './list-applications-users.controller';
import ApplicationsStrings from './applications.strings';

const MODULE_NAME = 'at.features.applications';

const addEditTemplate = require('~features/applications/add-edit-applications.view.html');
const listTemplate = require('~features/applications/list-applications.view.html');
const indexTemplate = require('~features/applications/index.view.html');
const userListTemplate = require('~features/applications/list-applications-users.view.html');

function ApplicationsDetailResolve (
    $q,
    $stateParams,
    Me,
    Application,
    Organization,
    ProcessErrors,
    strings
) {
    const id = $stateParams.application_id;

    const promises = {
        me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
    };

    if (!id) {
        promises.application = new Application('options');
        promises.organization = new Organization();

        return $q.all(promises);
    }

    promises.application = new Application(['get', 'options'], [id, id]);

    return $q.all(promises)
        .then(models => {
            const orgId = models.application.get('organization');

            const dependents = {
                organization: new Organization('get', orgId)
            };

            return $q.all(dependents)
                .then(related => {
                    models.organization = related.organization;

                    return models;
                });
        })
        .catch(({ data, status, config }) => {
            ProcessErrors(null, data, status, null, {
                hdr: strings.get('error.HEADER'),
                msg: strings.get('error.CALL', { path: `${config.url}`, status })
            });
            return $q.reject();
        });
}

ApplicationsDetailResolve.$inject = [
    '$q',
    '$stateParams',
    'MeModel',
    'ApplicationModel',
    'OrganizationModel',
    'ProcessErrors',
    'ApplicationsStrings'
];

function ApplicationsRun ($stateExtender, strings) {
    $stateExtender.addState({
        name: 'applications',
        route: '/applications',
        ncyBreadcrumb: {
            label: strings.get('state.LIST_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'o_auth2_application'
        },
        views: {
            '@': {
                templateUrl: indexTemplate,
            },
            'list@applications': {
                templateUrl: listTemplate,
                controller: ListController,
                controllerAs: 'vm'
            }
        },
        searchPrefix: 'application',
        params: {
            application_search: {
                value: {
                    page_size: 10,
                    order_by: 'name'
                }
            }
        },
        resolve: {
            resolvedModels: [
                'ApplicationModel',
                (Application) => {
                    const app = new Application(['options']);
                    return app;
                }
            ],
            Dataset: [
                '$stateParams',
                'Wait',
                'GetBasePath',
                'QuerySet',
                ($stateParams, Wait, GetBasePath, qs) => {
                    const searchParam = $stateParams.application_search;
                    const searchPath = GetBasePath('applications');

                    Wait('start');
                    return qs.search(searchPath, searchParam)
                        .finally(() => {
                            Wait('stop');
                        });
                }
            ],
        }
    });

    $stateExtender.addState({
        name: 'applications.add',
        route: '/add',
        ncyBreadcrumb: {
            label: strings.get('state.ADD_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'o_auth2_application'
        },
        views: {
            'add@applications': {
                templateUrl: addEditTemplate,
                controller: AddController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: ApplicationsDetailResolve
        }
    });

    $stateExtender.addState({
        name: 'applications.edit',
        route: '/:application_id',
        ncyBreadcrumb: {
            label: strings.get('state.EDIT_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'o_auth2_application',
            activityStreamId: 'application_id'
        },
        views: {
            'edit@applications': {
                templateUrl: addEditTemplate,
                controller: EditController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: ApplicationsDetailResolve
        }
    });

    $stateExtender.addState({
        name: 'applications.add.organization',
        url: '/organization?selected',
        searchPrefix: 'organization',
        params: {
            organization_search: {
                value: {
                    page_size: 5,
                    order_by: 'name',
                    role_level: 'admin_role'
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'organizations',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'organization@applications.add': {
                templateProvider: (ListDefinition, generateList) => {
                    const html = generateList.build({
                        mode: 'lookup',
                        list: ListDefinition,
                        input_type: 'radio'
                    });

                    return `<lookup-modal>${html}</lookup-modal>`;
                }
            }
        },
        resolve: {
            ListDefinition: ['OrganizationList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => qs.search(
                    GetBasePath('organizations'),
                    $stateParams[`${list.iterator}_search`]
                )
            ]
        },
        onExit ($state) {
            if ($state.transition) {
                $('#form-modal').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        }
    });

    $stateExtender.addState({
        name: 'applications.edit.organization',
        url: '/organization?selected',
        searchPrefix: 'organization',
        params: {
            organization_search: {
                value: {
                    page_size: 5,
                    order_by: 'name',
                    role_level: 'admin_role'
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'organizations',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'organization@applications.edit': {
                templateProvider: (ListDefinition, generateList) => {
                    const html = generateList.build({
                        mode: 'lookup',
                        list: ListDefinition,
                        input_type: 'radio'
                    });

                    return `<lookup-modal>${html}</lookup-modal>`;
                }
            }
        },
        resolve: {
            ListDefinition: ['OrganizationList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => qs.search(
                    GetBasePath('organizations'),
                    $stateParams[`${list.iterator}_search`]
                )
            ]
        },
        onExit ($state) {
            if ($state.transition) {
                $('#form-modal').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        }
    });

    $stateExtender.addState({
        name: 'applications.edit.users',
        route: '/users',
        ncyBreadcrumb: {
            label: strings.get('state.USER_LIST_BREADCRUMB_LABEL'),
            parent: 'applications.edit'
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'o_auth2_application'
        },
        views: {
            'userList@applications.edit': {
                templateUrl: userListTemplate,
                controller: UserListController,
                controllerAs: 'vm'
            }
        },
        params: {
            user_search: {
                value: {
                    order_by: 'user__username',
                    page_size: 10
                },
                dynamic: true
            }
        },
        searchPrefix: 'user',
        resolve: {
            resolvedModels: [
                'ApplicationModel',
                (Application) => {
                    const app = new Application(['options']);
                    return app;
                }
            ],
            Dataset: [
                '$stateParams',
                'Wait',
                'GetBasePath',
                'QuerySet',
                ($stateParams, Wait, GetBasePath, qs) => {
                    const searchParam = $stateParams.user_search;
                    const searchPath = `${GetBasePath('applications')}${$stateParams.application_id}/tokens`;

                    Wait('start');
                    return qs.search(searchPath, searchParam)
                        .finally(() => {
                            Wait('stop');
                        });
                }
            ],
        }
    });
}

ApplicationsRun.$inject = [
    '$stateExtender',
    'ApplicationsStrings'
];

angular
    .module(MODULE_NAME, [])
    .service('ApplicationsStrings', ApplicationsStrings)
    .run(ApplicationsRun);

export default MODULE_NAME;
