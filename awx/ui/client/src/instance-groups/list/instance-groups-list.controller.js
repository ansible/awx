export default [
    '$rootScope',
    '$scope',
    '$filter',
    '$state',
    'Alert',
    'resolvedModels',
    'Dataset',
    'InstanceGroupsStrings',
    'ProcessErrors',
    'Prompt',
    'Wait',
    function(
        $rootScope,
        $scope,
        $filter,
        $state,
        Alert,
        resolvedModels,
        Dataset,
        strings,
        ProcessErrors,
        Prompt,
        Wait
    ) {
        const vm = this;
        const { instanceGroup } = resolvedModels;
        let paginateQuerySet = {};

        vm.strings = strings;
        vm.isSuperuser = $scope.$root.user_is_superuser;

        init();

        function init(){
            $rootScope.breadcrumb.instance_group_name = $filter('sanitize')(instanceGroup.get('name'));
            $scope.list = {
                iterator: 'instance_group',
                name: 'instance_groups'
            };

            $scope.collection = {
                basePath: 'instance_groups',
                iterator: 'instance_group'
            };

            $scope[`${$scope.list.iterator}_dataset`] = Dataset.data;
            $scope[$scope.list.name] = $scope[`${$scope.list.iterator}_dataset`].results;
            $scope.instanceGroupCount = Dataset.data.count;

            $scope.$on('updateDataset', function(e, dataset, queryset) {
                $scope[`${$scope.list.iterator}_dataset`] = dataset;
                $scope[$scope.list.name] = dataset.results;
                paginateQuerySet = queryset;
            });
        }

        $scope.$watchCollection('$state.params', () => {
            vm.activeId = parseInt($state.params.instance_group_id);
            setToolbarSort();
        });

        const toolbarSortDefault = {
            label: `${strings.get('sort.NAME_ASCENDING')}`,
            value: 'name'
        };

        vm.toolbarSortOptions = [
            toolbarSortDefault,
            { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-name' },
            { label: `${strings.get('sort.CREATED_ASCENDING')}`, value: 'created' },
            { label: `${strings.get('sort.CREATED_DESCENDING')}`, value: '-created' },
            { label: `${strings.get('sort.MODIFIED_ASCENDING')}`, value: 'modified' },
            { label: `${strings.get('sort.MODIFIED_DESCENDING')}`, value: '-modified' }
        ];

        vm.toolbarSortValue = toolbarSortDefault;

        function setToolbarSort () {
            const orderByValue = _.get($state.params, 'instance_group_search.order_by');
            const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
            if (sortValue) {
                vm.toolbarSortValue = sortValue;
            } else {
                vm.toolbarSortValue = toolbarSortDefault;
            }
        }

        vm.onToolbarSort = (sort) => {
            vm.toolbarSortValue = sort;

            const queryParams = Object.assign(
                {},
                $state.params.instance_group_search,
                paginateQuerySet,
                { order_by: sort.value }
            );

            // Update URL with params
            $state.go('.', {
                instance_group_search: queryParams
            }, { notify: false, location: 'replace' });
        };

        vm.tooltips = {
            add: strings.get('tooltips.ADD_INSTANCE_GROUP')
        };

        vm.rowAction = {
            trash: instance_group => {
                return vm.isSuperuser && instance_group.name !== 'tower' && !instance_group.is_controller && !instance_group.is_isolated;
            }
        };

        vm.deleteInstanceGroup = instance_group => {
            if (!instance_group) {
                Alert(strings.get('error.DELETE'), strings.get('alert.MISSING_PARAMETER'));
                return;
            }

            Prompt({
                action() {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    instanceGroup
                        .request('delete', instance_group.id)
                        .then(() => handleSuccessfulDelete(instance_group))
                        .catch(createErrorHandler('delete instance group', 'DELETE'))
                        .finally(() => Wait('stop'));
                },
                hdr: strings.get('DELETE'),
                resourceName: $filter('sanitize')(instance_group.name),
                body: `${strings.get('deleteResource.CONFIRM', 'instance group')}`
            });
        };

        function handleSuccessfulDelete(instance_group) {
            let reloadListStateParams = null;

            if($scope.instance_groups.length === 1 && $state.params.instance_group_search && _.has($state, 'params.instance_group_search.page') && $state.params.instance_group_search.page !== '1') {
                reloadListStateParams = _.cloneDeep($state.params);
                reloadListStateParams.instance_group_search.page = (parseInt(reloadListStateParams.instance_group_search.page)-1).toString();
            }

            if (parseInt($state.params.instance_group_id, 0) === instance_group.id) {
                $state.go('instanceGroups', reloadListStateParams, { reload: true });
            } else {
                $state.go('.', reloadListStateParams, { reload: true });
            }
        }

        function createErrorHandler(path, action) {
            return ({ data, status }) => {
                const hdr = strings.get('error.HEADER');
                const msg = strings.get('error.CALL', { path, action, status });
                ProcessErrors($scope, data, status, null, { hdr, msg });
            };
        }

        $scope.createInstanceGroup = () => {
            $state.go('instanceGroups.add');
        };
    }
];
