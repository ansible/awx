function AddContainerGroupController(ToJSON, $scope, $state, models, strings, i18n, DataSet) {
  const vm = this || {};
  const {
    instanceGroup,
    credential
  } = models;

  vm.mode = 'add';
  vm.strings = strings;
  vm.panelTitle = strings.get('state.ADD_CONTAINER_GROUP_BREADCRUMB_LABEL');
  vm.lookUpTitle = strings.get('container.LOOK_UP_TITLE');

  vm.docs = {
    url: 'https://docs.ansible.com/ansible-tower/latest/html/administration/external_execution_envs.html#ag-container-groups',
    help_text: vm.strings.get('tooltips.CG_DOCS_HELP_TEXT')
  };

  vm.form = instanceGroup.createFormSchema('post');
  vm.form.name.required = true;
  delete vm.form.name.help_text;

  vm.form.credential = {
    type: 'field',
    label: i18n._('Credential'),
    id: 'credential'
  };
  vm.form.credential._resource = 'credential';
  vm.form.credential._route = "instanceGroups.addContainerGroup.credentials";
  vm.form.credential._model = credential;
  vm.form.credential._placeholder = strings.get('container.CREDENTIAL_PLACEHOLDER');
  vm.form.credential.help_text = strings.get('container.CREDENTIAL_HELP_TEXT');
  vm.form.credential.required = true;

  vm.form.extraVars = {
    label: strings.get('container.POD_SPEC_LABEL'),
    value: DataSet.data.actions.POST.pod_spec_override.default,
    name: 'extraVars',
    toggleLabel: strings.get('container.POD_SPEC_TOGGLE'),
    tooltip: strings.get('container.EXTRA_VARS_HELP_TEXT')
  };

  vm.tab = {
    details: { _active: true },
    instances: {_disabled: true },
    jobs: {_disabled: true }
};

  $scope.variables = vm.form.extraVars.value;
  $scope.name = vm.form.extraVars.name;
  vm.panelTitle = strings.get('container.PANEL_TITLE');


  $scope.$watch('credential', () => {
    if ($scope.credential) {
        vm.form.credential._idFromModal= $scope.credential;
      }
  });
  vm.form.save = (data) => {
    data.pod_spec_override = null;
    if (vm.form.extraVars.isOpen) {
      data.pod_spec_override = vm.form.extraVars.value;
    }
    return instanceGroup.request('post', { data: data }).then((res) => {
      $state.go('instanceGroups.editContainerGroup', { instance_group_id: res.data.id }, { reload: true });
    });
  };
  vm.form.extraVars.isOpen = false;
  vm.toggle = () => {
    if (vm.form.extraVars.isOpen === true) {
      vm.form.extraVars.isOpen = false;
    } else {
      vm.form.extraVars.isOpen = true;
    }
    return vm.form.extraVars.isOpen;
  };
}


AddContainerGroupController.$inject = [
  'ToJSON',
  '$scope',
  '$state',
  'resolvedModels',
  'InstanceGroupsStrings',
  'i18n',
  'DataSet'
];

export default AddContainerGroupController;
