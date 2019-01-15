export default ['templateUrl', '$window', function(templateUrl, $window) {
    return {
        restrict: 'E',
        scope: {
            instanceGroups: '='
        },
        templateUrl: templateUrl('shared/instance-groups-multiselect/instance-groups-modal/instance-groups-modal'),

        link: function(scope, element) {

            $('#instance-groups-modal').on('hidden.bs.modal', function () {
                $('#instance-groups-modal').off('hidden.bs.modal');
                $(element).remove();
            });

            scope.showModal = function() {
                $('#instance-groups-modal').modal('show');
            };

            scope.destroyModal = function() {
                $('#instance-groups-modal').modal('hide');
            };
        },

        controller: ['$scope', '$compile', 'QuerySet', 'GetBasePath','generateList', 'InstanceGroupList', function($scope, $compile, qs, GetBasePath, GenerateList, InstanceGroupList) {

            function init() {

                    $scope.instance_group_queryset = {
                        order_by: 'name',
                        page_size: 5
                    };

                    $scope.instance_group_default_params = {
                        order_by: 'name',
                        page_size: 5
                    };

                    qs.search(GetBasePath('instance_groups'), $scope.instance_group_queryset)
                        .then(res => {
                            $scope.instance_group_dataset = res.data;
                            $scope.instance_groups = $scope.instance_group_dataset.results;

                            let instanceGroupList = _.cloneDeep(InstanceGroupList);

                            instanceGroupList.listTitle = false;
                            instanceGroupList.well = false;
                            instanceGroupList.multiSelect = true;
                            instanceGroupList.multiSelectPreview = {
                                selectedRows: 'igTags',
                                availableRows: 'instance_groups'
                            };
                            instanceGroupList.fields.name.ngClick = "linkoutInstanceGroup(instance_group)";
                            instanceGroupList.fields.name.columnClass = 'col-md-11 col-sm-11 col-xs-11';
                            delete instanceGroupList.fields.consumed_capacity;
                            delete instanceGroupList.fields.jobs_running;

                            let html = `${GenerateList.build({
                                list: instanceGroupList,
                                input_type: 'instance-groups-modal-body',
                                hideViewPerPage: true,
                                mode: 'lookup'
                            })}`;

                            $scope.list = instanceGroupList;
                            $('#instance-groups-modal-body').append($compile(html)($scope));

                            if ($scope.instanceGroups) {
                                $scope.instanceGroups = $scope.instanceGroups.map( (item) => {
                                    item.isSelected = true;
                                    if (!$scope.igTags) {
                                        $scope.igTags = [];
                                    }
                                    $scope.igTags.push(item);
                                    return item;
                                });
                            }

                            $scope.showModal();
                    });

                    $scope.$watch('instance_groups', function(){
                        angular.forEach($scope.instance_groups, function(instanceGroupRow) {
                            angular.forEach($scope.igTags, function(selectedInstanceGroup){
                                if(selectedInstanceGroup.id === instanceGroupRow.id) {
                                    instanceGroupRow.isSelected = true;
                                }
                            });
                        });
                    });
            }

            init();

            $scope.$on("selectedOrDeselected", function(e, value) {
                let item = value.value;
                if (value.isSelected) {
                    if(!$scope.igTags) {
                        $scope.igTags = [];
                    }
                    $scope.igTags.push(item);
                } else {
                    _.remove($scope.igTags, { id: item.id });
                }
            });

            $scope.linkoutInstanceGroup = function(instanceGroup) {
                $window.open('/#/instance_groups/' + instanceGroup.id + '/instances','_blank');
            };

            $scope.cancelForm = function() {
                $scope.destroyModal();
            };

            $scope.saveForm = function() {
                $scope.instanceGroups = $scope.igTags;
                $scope.destroyModal();
            };
        }]
    };
}];
