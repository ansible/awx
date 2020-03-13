/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['$scope', '$rootScope', 'ProcessErrors', 'GetBasePath', 'generateList',
 '$state', 'Rest', '$q', 'Wait', '$window', 'QuerySet', 'GroupList', 'i18n',
 function($scope, $rootScope, ProcessErrors, GetBasePath, generateList,
     $state, Rest, $q, Wait, $window, qs, GroupList, i18n) {
     $scope.$on("linkLists", function() {

         init();

         function init(){
             $scope.appStrings = $rootScope.appStrings;
             $scope.associate_group_default_params = {
                 order_by: 'name',
                 page_size: 5
             };

             $scope.associate_group_queryset = {
                 order_by: 'name',
                 page_size: 5
             };

             if ($state.params.group_id) {
                 $scope.associate_group_default_params.not__id = $state.params.group_id;
                 $scope.associate_group_queryset.not__id = $state.params.group_id;
                 $scope.associate_group_default_params.not__parents = $state.params.group_id;
                 $scope.associate_group_queryset.not__parents = $state.params.group_id;
             } else if ($state.params.host_id) {
                 $scope.associate_group_default_params.not__hosts = $state.params.host_id;
                 $scope.associate_group_queryset.not__hosts = $state.params.host_id;
             }

             let list = _.cloneDeep(GroupList);
             list.basePath = GetBasePath('inventory') + $state.params.inventory_id + '/groups';
             list.iterator = 'associate_group';
             list.name = 'associate_groups';
             list.multiSelect = true;
             list.fields.name.ngClick = 'linkoutGroup(associate_group)';
             list.trackBy = 'associate_group.id';
             list.multiSelectPreview = {
                 selectedRows: 'selectedItems',
                 availableRows: 'associate_groups'
             };
             list.emptyListText = i18n._('No groups to add');
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
                         title: false,
                         hideViewPerPage: true
                     });

                     $scope.compileList(html);

                     $scope.$watchCollection('associate_groups', function () {
                         if($scope.selectedItems) {
                             $scope.associate_groups.forEach(function(row, i) {
                                 if ($scope.selectedItems.filter(function(e) { return e.id === row.id; }).length > 0) {
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
                     $scope.selectedItems.push(item);
                 }
                 else {
                     // _.remove() Returns the new array of removed elements.
                     // This will pull all the values out of the array that don't
                     // match the deselected item effectively removing it
                     $scope.selectedItems = _.remove($scope.selectedItems, function(selectedItem) {
                         return selectedItem.id !== item.id;
                     });
                 }
             });
         }

         $scope.linkGroups = function() {
             $scope.saveFunction({selectedItems: $scope.selectedItems})
                 .then(() =>{
                     $scope.closeModal();
                 }).catch(() => {
                     $scope.closeModal();
                 });

         };

         $scope.linkoutGroup = function(group) {
             $window.open('/#/inventories/inventory/' + group.inventory + '/groups/edit/' + group.id,'_blank');
         };
     });
 }];
