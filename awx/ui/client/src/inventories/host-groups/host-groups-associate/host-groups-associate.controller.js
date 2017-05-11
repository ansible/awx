/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['$scope', '$rootScope', 'ProcessErrors', 'GetBasePath', 'generateList',
 '$state', 'Rest', '$q', 'Wait', '$window', 'QuerySet', 'GroupList', 'HostManageService',
 function($scope, $rootScope, ProcessErrors, GetBasePath, generateList,
     $state, Rest, $q, Wait, $window, qs, GroupList, HostManageService) {
     $scope.$on("linkLists", function() {

         init();

         function init(){
             $scope.associate_group_default_params = {
                 order_by: 'name',
                 page_size: 5
             };

             $scope.associate_group_queryset = {
                 order_by: 'name',
                 page_size: 5
             };

             let list = _.cloneDeep(GroupList);
             list.basePath = GetBasePath('inventory') + $state.params.inventory_id + '/groups';
             list.iterator = 'associate_group';
             list.name = 'associate_groups';
             list.multiSelect = true;
             list.fields.name.ngClick = 'linkoutHostGroup(associate_group.id)';
             list.trackBy = 'associate_group.id';
             delete list.actions;
             delete list.fieldActions;
             delete list.fields.failed_hosts;
             list.well = false;
             $scope.list = list;

             // Fire off the initial search
             qs.search(list.basePath, $scope.associate_group_default_params)
                 .then(function(res) {
                     $scope.associate_group_dataset = res.data;
                     $scope.associate_groups = $scope.associate_group_dataset.results;

                     let html = generateList.build({
                         list: list,
                         mode: 'edit',
                         title: false
                     });

                     $scope.compileList(html);

                     $scope.$watchCollection('associate_groups', function () {
                         if($scope.selectedItems) {
                             $scope.associate_groups.forEach(function(row, i) {
                                 if (_.includes($scope.selectedItems, row.id)) {
                                     $scope.associate_groups[i].isSelected = true;
                                 }
                             });
                         }
                     });

                 });

             $scope.selectedItems = [];
             $scope.$on('selectedOrDeselected', function(e, value) {
                 let item = value.value;

                 if (value.isSelected) {
                     $scope.selectedItems.push(item.id);
                 }
                 else {
                     // _.remove() Returns the new array of removed elements.
                     // This will pull all the values out of the array that don't
                     // match the deselected item effectively removing it
                     $scope.selectedItems = _.remove($scope.selectedItems, function(selectedItem) {
                         return selectedItem !== item.id;
                     });
                 }
             });
         }

         $scope.linkHostGroup = function() {
            //  HostManageService.associateGroup(host, $scope.disassociateGroup.id).then(() => {
            //      $state.go($state.current, null, {reload: true});
            //      $('#host-disassociate-modal').modal('hide');
            //      $('body').removeClass('modal-open');
            //      $('.modal-backdrop').remove();
            //  });

             $q.all( _.map($scope.selectedItems, (id) => HostManageService.associateGroup({id: $state.params.host_id}, id)) )
                 .then( () =>{
                     Wait('stop');
                     $scope.closeModal();
                 }, (error) => {
                     $scope.closeModal();
                     ProcessErrors(null, error.data, error.status, null, {
                         hdr: 'Error!',
                         msg: 'Failed to associate host to group(s): POST returned status' +
                             error.status
                     });
                 });
         };

         $scope.linkoutHostGroup = function(userId) {
             // Open the edit user form in a new tab so as not to navigate the user
             // away from the modal
             $window.open('/#/users/' + userId,'_blank');
         };
     });
 }];
