/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default ['$scope', '$rootScope', 'ProcessErrors', 'GetBasePath', 'generateList',
 '$state', 'Rest', '$q', 'Wait', '$window', 'QuerySet', 'RelatedHostsListDefinition', 'i18n',
 function($scope, $rootScope, ProcessErrors, GetBasePath, generateList,
     $state, Rest, $q, Wait, $window, qs, RelatedHostsListDefinition, i18n) {
     $scope.$on("linkLists", function() {

         init();

         function init(){
             $scope.appStrings = $rootScope.appStrings;
             $scope.associate_host_default_params = {
                 order_by: 'name',
                 page_size: 5
             };

             $scope.associate_host_queryset = {
                 order_by: 'name',
                 page_size: 5
             };

             if ($state.params.group_id) {
                 $scope.associate_host_default_params.not__groups = $state.params.group_id;
                 $scope.associate_host_queryset.not__groups = $state.params.group_id;
             }

             let list = _.cloneDeep(RelatedHostsListDefinition);
             list.basePath = GetBasePath('inventory') + $state.params.inventory_id + '/hosts';
             list.iterator = 'associate_host';
             list.name = 'associate_hosts';
             list.multiSelect = true;
             list.fields.name.ngClick = 'linkoutHost(associate_host)';
             list.fields.name.ngClass = "{ 'host-disabled-label': !associate_host.enabled }";
             list.fields.name.dataHostId = "{{ associate_host.id }}";
             list.trackBy = 'associate_host.id';
             list.multiSelectPreview = {
                 selectedRows: 'selectedItems',
                 availableRows: 'associate_hosts'
             };
             list.emptyListText = i18n._('No hosts to add');
             delete list.fields.toggleHost;
             delete list.fields.active_failures;
             delete list.fields.groups;
             delete list.actions;
             delete list.fieldActions;
             list.well = false;
             $scope.list = list;

             // Fire off the initial search
             qs.search(list.basePath, $scope.associate_host_default_params)
                 .then(function(res) {
                     $scope.associate_host_dataset = res.data;
                     $scope.associate_hosts = $scope.associate_host_dataset.results;

                     let html = generateList.build({
                         list: list,
                         mode: 'edit',
                         title: false,
                         hideViewPerPage: true
                     });

                     $scope.compileList(html);

                     $scope.$watchCollection('associate_hosts', function () {
                         if($scope.selectedItems) {
                             $scope.associate_hosts.forEach(function(row, i) {
                                 if ($scope.selectedItems.filter(function(e) { return e.id === row.id; }).length > 0) {
                                     $scope.associate_hosts[i].isSelected = true;
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

         $scope.linkhosts = function() {
             $scope.saveFunction({selectedItems: $scope.selectedItems})
                 .then(() =>{
                     $scope.closeModal();
                 }).catch(() => {
                     $scope.closeModal();
                 });

         };

         $scope.linkoutHost = function(host) {
             $window.open('/#/inventories/inventory/' + host.inventory + '/hosts/edit/' + host.id,'_blank');
         };
     });
 }];
