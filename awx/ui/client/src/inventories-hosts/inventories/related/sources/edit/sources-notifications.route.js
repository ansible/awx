import { N_ } from '../../../../../i18n';

export default {
    searchPrefix: 'notification',
    name: "inventories.edit.inventory_sources.edit.notifications",
    url: `/notifications`,
    ncyBreadcrumb: {
        parent: "inventories.edit.inventory_sources.edit",
        label: N_("NOTIFICATIONS")
    },
    params: {
        [ 'notification_search']: {
            value: { order_by: 'name' }
        }
    },
    views: {
        'related': {
            templateProvider: function(FormDefinition, GenerateForm, $stateParams, SourcesFormDefinition) {
                var form, html;
                if($stateParams && $stateParams.inventory_source_id){
                    form = SourcesFormDefinition;
                }
                else {
                    form = typeof(FormDefinition) === 'function' ?
                        FormDefinition() : FormDefinition;
                }
                html = GenerateForm.buildCollection({
                    mode: 'edit',
                    related: `notifications`,
                    form: form
                });
                return html;
            },
            controller: ['$scope', 'NotificationsList', 'Dataset', 'ToggleNotification', 'NotificationsListInit', 'GetBasePath', '$stateParams',
                function($scope, list, Dataset, ToggleNotification, NotificationsListInit, GetBasePath, $stateParams) {
                    var params = $stateParams,
                    id = params.inventory_source_id,
                    url = GetBasePath('inventory_sources');

                    function init() {
                        $scope.list = list;
                        $scope[`${list.iterator}_dataset`] = Dataset.data;
                        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;


                        NotificationsListInit({
                            scope: $scope,
                            url: url,
                            id: id
                        });

                        $scope.$watch(`${list.iterator}_dataset`, function() {
                            // The list data has changed and we need to update which notifications are on/off
                            $scope.$emit('relatednotifications');
                        });
                    }

                    $scope.toggleNotification = function(event, notifier_id, column) {
                        var notifier = this.notification;
                        try {
                            $(event.target).tooltip('hide');
                        }
                        catch(e) {
                            // ignore
                        }
                        ToggleNotification({
                            scope: $scope,
                            url: url + id,
                            notifier: notifier,
                            column: column,
                            callback: 'NotificationRefresh'
                        });
                    };

                    init();

                }
            ]
        }
    },
    resolve: {
        Dataset: ['NotificationsList', 'QuerySet', '$stateParams', 'GetBasePath',
            (list, qs, $stateParams, GetBasePath) => {
                let path = GetBasePath(list.basePath);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
