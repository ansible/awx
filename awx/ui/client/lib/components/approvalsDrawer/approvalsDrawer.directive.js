const templateUrl = require('~components/approvalsDrawer/approvalsDrawer.partial.html');

function AtApprovalsDrawerController (strings, Rest, GetBasePath, $rootScope) {
    const vm = this || {};

    const toolbarSortDefault = {
        label: `${strings.get('sort.CREATED_ASCENDING')}`,
        value: 'created'
    };

    vm.strings = strings;
    vm.toolbarSortValue = toolbarSortDefault;
    vm.queryset = {
        page: 1,
        page_size: 5,
        order_by: 'created',
        status: 'pending'
    };
    vm.emptyListReason = vm.strings.get('approvals.NONE');

    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${vm.strings.get('sort.CREATED_DESCENDING')}`, value: '-created' }
    ];

    const loadTheList = () => {
        const queryParams = Object.keys(vm.queryset).map(key => `${key}=${vm.queryset[key]}`).join('&');
        Rest.setUrl(`${GetBasePath('workflow_approvals')}?${queryParams}`);
        return Rest.get()
            .then(({ data }) => {
                vm.dataset = data;
                vm.approvals = data.results;
                vm.count = data.count;
                $rootScope.pendingApprovalCount = data.count;
            });
    };

    loadTheList()
        .then(() => { vm.listLoaded = true; });

    vm.approve = (approval) => {
        Rest.setUrl(`${GetBasePath('workflow_approvals')}${approval.id}/approve`);
        Rest.post()
            .then(() => loadTheList());
    };

    vm.deny = (approval) => {
        Rest.setUrl(`${GetBasePath('workflow_approvals')}${approval.id}/deny`);
        Rest.post()
            .then(() => loadTheList());
    };

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;
        vm.queryset.page = 1;
        vm.queryset.order_by = sort.value;
        loadTheList();
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
