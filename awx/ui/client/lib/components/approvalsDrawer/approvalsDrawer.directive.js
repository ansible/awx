const templateUrl = require('~components/approvalsDrawer/approvalsDrawer.partial.html');

function AtApprovalsDrawerController (strings, Rest, GetBasePath, $rootScope) {
    const vm = this || {};

    const toolbarSortDefault = {
        label: `${strings.get('sort.CREATED_ASCENDING')}`,
        value: 'created'
    };

    vm.toolbarSortValue = toolbarSortDefault;

    // This will probably need to be expanded
    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.CREATED_DESCENDING')}`, value: '-created' }
    ];

    vm.queryset = {
        page_size: 5
    };

    vm.emptyListReason = strings.get('approvals.NONE');

    const loadTheList = () => {
        Rest.setUrl(`${GetBasePath('workflow_approval')}?page_size=5&order_by=created&status=pending`);
        Rest.get()
            .then(({ data }) => {
                vm.dataset = data;
                vm.approvals = data.results;
                vm.count = data.count;
                $rootScope.pendingApprovalCount = data.count;
                vm.listLoaded = true;
            });
    };

    loadTheList();

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;

        // TODO: this...
        // const queryParams = Object.assign(
        //     {},
        //     $state.params.user_search,
        //     paginateQuerySet,
        //     { order_by: sort.value }
        // );

        // // Update URL with params
        // $state.go('.', {
        //     user_search: queryParams
        // }, { notify: false, location: 'replace' });

        // rather than ^^ we want to just re-load the data based on new params
    };

    vm.approve = (approval) => {
        Rest.setUrl(`${GetBasePath('workflow_approval')}${approval.id}/approve`);
        Rest.post()
            .then(() => loadTheList());
    };

    vm.deny = (approval) => {
        Rest.setUrl(`${GetBasePath('workflow_approval')}${approval.id}/deny`);
        Rest.post()
            .then(() => loadTheList());
    };
}

AtApprovalsDrawerController.$inject = ['ComponentsStrings', 'Rest', 'GetBasePath', '$rootScope'];

function atApprovalsDrawer () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl,
        controller: AtApprovalsDrawerController,
        controllerAs: 'vm',
        scope: {
            closeApprovals: '&'
        },
    };
}

export default atApprovalsDrawer;
