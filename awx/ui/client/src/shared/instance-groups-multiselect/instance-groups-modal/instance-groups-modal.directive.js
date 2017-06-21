export default ['templateUrl', function(templateUrl) {
    return {
        restrict: 'E',
        scope: {
            instanceGroups: '='
        },
        templateUrl: templateUrl('instance-groups/instance-groups-multiselect/instance-groups-modal/instance-groups-modal'),

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

                    qs.search(GetBasePath('instance_groups'), $scope.instance_groups_queryset)
                        .then(res => {
                            $scope.instance_group_dataset = res.data;
                            $scope.instance_groups = $scope.instance_group_dataset.results;

                            let instanceGroupList = _.cloneDeep(InstanceGroupList);

                            instanceGroupList.listTitle = false;
                            instanceGroupList.well = false;
                            instanceGroupList.multiSelect = true;
                            instanceGroupList.multiSelectExtended = true;
                            delete instanceGroupList.fields.percent_capacity_remaining;
                            delete instanceGroupList.fields.jobs_running;

                            let html = `${GenerateList.build({
                                list: instanceGroupList,
                                input_type: 'instance-groups-modal-body'
                            })}`;

                            $scope.list = instanceGroupList;
                            $('#instance-groups-modal-body').append($compile(html)($scope));

                            if ($scope.instanceGroups) {
                                $scope.instance_groups.map( (item) => {
                                    isSelected(item);
                                });
                            }

                            $scope.showModal();
                    });

            }

            init();

            function isSelected(item) {
                if(_.find($scope.instanceGroups, {id: item.id})){
                    item.isSelected = true;
                    if (!$scope.igTags) {
                        $scope.igTags = [];
                    }
                    $scope.igTags.push(item);
                }
                return item;
            }

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