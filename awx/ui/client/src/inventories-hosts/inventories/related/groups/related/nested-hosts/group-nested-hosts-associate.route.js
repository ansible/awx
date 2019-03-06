export default {
    name: 'inventories.edit.groups.edit.nested_hosts.associate',
    squashSearchUrl: true,
    url: '/associate',
    ncyBreadcrumb:{
        skip:true
    },
    views: {
        'modal@^.^': {
            templateProvider: function() {
                return `<associate-hosts save-function="associateHosts(selectedItems)"></associate-hosts>`;
            },
            controller: function($scope, $q, GroupsService, $state){
                $scope.associateHosts = function(selectedItems){
                    var deferred = $q.defer();
                    return $q.all( _.map(selectedItems, (selectedItem) => GroupsService.associateHost({id: selectedItem.id}, $state.params.group_id)) )
                         .then( () =>{
                             deferred.resolve();
                         }, (error) => {
                             deferred.reject(error);
                         });
                };
            }
        }
    },
    onExit: function($state) {
        if ($state.transition) {
            $('#associate-groups-modal').modal('hide');
            $('body').removeClass('modal-open');
        }
    },
};
