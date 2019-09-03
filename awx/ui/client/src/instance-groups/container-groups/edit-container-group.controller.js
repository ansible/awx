function EditContainerGroupController($rootScope, $scope, $state, models, strings, i18n, EditContainerGroupDataset) {
  const vm = this || {};
  const {
    instanceGroup,
    credential
  } = models;

  if (!instanceGroup.get('is_containerized')) {
      return $state.go(
          'instanceGroups.edit',
          { instance_group_id: instanceGroup.get('id') },
          { reload: true }
      );
  }

  $rootScope.breadcrumb.instance_group_name = instanceGroup.get('name');

  vm.mode = 'edit';
  vm.strings = strings;
  vm.panelTitle = EditContainerGroupDataset.data.name;
  vm.lookUpTitle = strings.get('container.LOOK_UP_TITLE');

  vm.form = instanceGroup.createFormSchema('post');
  vm.form.name.required = true;
  vm.form.credential = {
    type: 'field',
    label: i18n._('Credential'),
    id: 'credential'
  };
  vm.form.credential._resource = 'credential';
  vm.form.credential._route = "instanceGroups.editContainerGroup.credentials";
  vm.form.credential._model = credential;
  vm.form.credential._displayValue = EditContainerGroupDataset.data.summary_fields.credential.name;
  vm.form.credential.required = true;
  vm.form.credential._value = EditContainerGroupDataset.data.summary_fields.credential.id;

  vm.tab = {
    details: {
            _active: true,
            _go: 'instanceGroups.editContainerGroup',
            _params: { instance_group_id: instanceGroup.get('id') }
    },
    instances: {
        _go: 'instanceGroups.containerGroupInstances',
        _params: { instance_group_id: instanceGroup.get('id') }
    },
    jobs: {
        _go: 'instanceGroups.containerGroupJobs',
        _params: { instance_group_id: instanceGroup.get('id') }
    }
};

  vm.form.extraVars = {
    label: strings.get('container.POD_SPEC_LABEL'),
    value: EditContainerGroupDataset.data.pod_spec_override,
    name: 'extraVars',
    toggleLabel: strings.get('container.POD_SPEC_TOGGLE')
  };

  if (vm.form.extraVars.value) {
    vm.form.extraVars.isOpen = true;
  } else {
    vm.form.extraVars.isOpen = false;
  }

  $scope.$watch('credential', () => {
    if ($scope.credential) {
      vm.form.credential._idFromModal= $scope.credential;
      }
  });
  vm.form.save = (data) => {
    if (vm.form.extraVars.value === '---') {
      data.pod_spec_override = null;
    } else {
      data.pod_spec_override = vm.form.extraVars.value;
    }
    return instanceGroup.request('put', { data: data }).then((res) => {
      $state.go('instanceGroups.editContainerGroup', { instance_group_id: res.data.id }, { reload: true });
    } );
  };

  vm.toggle = () => {
    if (vm.form.extraVars.isOpen === true) {
      vm.form.extraVars.isOpen = false;
    } else {
      vm.form.extraVars.isOpen = true;
    }
    return vm.form.extraVars.isOpen;
  };
}

EditContainerGroupController.$inject = [
  '$rootScope',
  '$scope',
  '$state',
  'resolvedModels',
  'InstanceGroupsStrings',
  'i18n',
  'EditContainerGroupDataset'
];

export default EditContainerGroupController;
