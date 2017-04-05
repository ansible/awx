/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function HostsList($scope, HostsNewList, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait, HostManageService) {

    let list = HostsNewList;

    init();

    function init(){
        $scope.canAdd = false;

        rbacUiControlService.canAdd('hosts')
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $rootScope.flashMessage = null;

    }

    $scope.createHost = function(){
        $state.go('hostsnew.add');
    };
    $scope.editHost = function(id){
        $state.go('hostsnew.edit', {host_id: id});
    };
    $scope.deleteHost = function(id, name){
        var body = '<div class=\"Prompt-bodyQuery\">Are you sure you want to permanently delete the host below from the inventory?</div><div class=\"Prompt-bodyTarget\">' + $filter('sanitize')(name) + '</div>';
        var action = function(){
            delete $rootScope.promptActionBtnClass;
            Wait('start');
            HostManageService.delete(id).then(() => {
                $('#prompt-modal').modal('hide');
                if (parseInt($state.params.host_id) === id) {
                    $state.go("hostsnew", null, {reload: true});
                } else {
                    $state.go($state.current.name, null, {reload: true});
                }
                Wait('stop');
            });
        };
        // Prompt depends on having $rootScope.promptActionBtnClass available...
        Prompt({
            hdr: 'Delete Host',
            body: body,
            action: action,
            actionText: 'DELETE',
        });
        $rootScope.promptActionBtnClass = 'Modal-errorButton';
    };

    $scope.toggleHost = function(event, host) {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }

        host.enabled = !host.enabled;

        HostManageService.put(host).then(function(){
            $state.go($state.current, null, {reload: true});
        });
    };

}

export default ['$scope', 'HostsNewList', '$rootScope', 'GetBasePath',
    'rbacUiControlService', 'Dataset', '$state', '$filter', 'Prompt', 'Wait', 'HostManageService', HostsList
];
