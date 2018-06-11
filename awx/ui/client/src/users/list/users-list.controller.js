/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { N_ } from "../../i18n";

const user_type_options = [
 { type: 'normal', label: N_('Normal User') },
 { type: 'system_auditor', label: N_('System Auditor') },
 { type: 'system_administrator', label: N_('System Administrator') },
];

export default ['$scope', '$rootScope', 'Rest', 'UserList', 'Prompt',
    'ProcessErrors', 'GetBasePath', 'Wait', '$state', '$filter',
    'rbacUiControlService', 'Dataset', 'i18n', 'resolvedModels',
    function($scope, $rootScope, Rest, UserList, Prompt,
    ProcessErrors, GetBasePath, Wait, $state, $filter, rbacUiControlService,
    Dataset, i18n, models) {

        for (var i = 0; i < user_type_options.length; i++) {
            user_type_options[i].label = i18n._(user_type_options[i].label);
        }

        const { me } = models;
        var list = UserList,
        defaultUrl = GetBasePath('users');

        init();

        function init() {
            $scope.canEdit = me.get('summary_fields.user_capabilities.edit');
            $scope.canAdd = false;

            rbacUiControlService.canAdd('users')
                .then(function(params) {
                    $scope.canAdd = params.canAdd;
                });

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;


            $rootScope.flashMessage = null;
            $scope.selected = [];
        }

        $scope.addUser = function() {
            $state.go('users.add');
        };

        $scope.editUser = function(id) {
            $state.go('users.edit', { user_id: id });
        };

        $scope.deleteUser = function(id, name) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.destroy()
                    .then(() => {

                        let reloadListStateParams = null;

                        if($scope.users.length === 1 && $state.params.user_search && _.has($state, 'params.user_search.page') && $state.params.user_search.page !== '1') {
                            reloadListStateParams = _.cloneDeep($state.params);
                            reloadListStateParams.user_search.page = (parseInt(reloadListStateParams.user_search.page)-1).toString();
                        }

                        if (parseInt($state.params.user_id) === id) {
                            $state.go('^', null, { reload: true });
                        } else {
                            $state.go('.', null, { reload: true });
                        }
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: i18n._('Error!'),
                            msg: i18n.sprintf(i18n._('Call to %s failed. DELETE returned status: '), url) + status
                        });
                    });
            };

            Prompt({
                hdr: i18n._('Delete'),
                resourceName: $filter('sanitize')(name),
                body: '<div class="Prompt-bodyQuery">' + i18n._('Are you sure you want to delete this user?') + '</div>',
                action: action,
                actionText: i18n._('DELETE')
            });
        };
    }
];
