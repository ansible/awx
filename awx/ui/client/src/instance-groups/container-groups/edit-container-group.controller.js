function EditContainerGroupController($rootScope, $scope, $state, models, strings, i18n, EditContainerGroupDataset) {
  const vm = this || {};
  const {
    instanceGroup,
    credential
  } = models;
  let canEdit = false;
  if (instanceGroup.has('options', 'actions.PUT')) {
    canEdit = instanceGroup.model.OPTIONS.actions.PUT;
}
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

  vm.docs = {
    url: 'https://docs.ansible.com/ansible-tower/latest/html/administration/external_execution_envs.html#ag-container-groups',
    help_text: vm.strings.get('tooltips.CG_DOCS_HELP_TEXT')
  };

  vm.form = instanceGroup.createFormSchema('post');
  vm.switchDisabled = false;
  vm.form.disabled = !instanceGroup.has('options', 'actions.PUT');
  vm.form.name.required = true;
  delete vm.form.name.help_text;
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
  vm.form.credential.help_text = strings.get('container.CREDENTIAL_HELP_TEXT');

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
  if (!canEdit) {
    vm.form.extraVars = {
      label: strings.get('container.POD_SPEC_LABEL'),
      value: EditContainerGroupDataset.data.pod_spec_override || "---",
      name: 'extraVars',
      disabled: true,
      tooltip: strings.get('container.EXTRA_VARS_HELP_TEXT')
    };
    vm.switchDisabled = true;
  } else {
    vm.form.extraVars = {
      label: strings.get('container.POD_SPEC_LABEL'),
      value: EditContainerGroupDataset.data.pod_spec_override || instanceGroup.model.OPTIONS.actions.PUT.pod_spec_override.default,
      name: 'extraVars',
      toggleLabel: strings.get('container.POD_SPEC_TOGGLE'),
      tooltip: strings.get('container.EXTRA_VARS_HELP_TEXT')
    };
  }

  function sanitizeVars (str) {
    // Quick function to test if the host vars are a json-object-string,
    // by testing if they can be converted to a JSON object w/o error.
    function IsJsonString (varStr) {
      try {
        JSON.parse(varStr);
      } catch (e) {
        return false;
      }
      return true;
    }

    if (typeof str === 'undefined') {
      return '---';
    }
    if (typeof str !== 'string') {
      const yamlStr = jsyaml.safeDump(str);
      // jsyaml.safeDump doesn't process an empty object correctly
      if (yamlStr === '{}\n') {
        return '---';
      }
      return yamlStr;
    }
    if (str === '' || str === '{}') {
      return '---';
    } else if (IsJsonString(str)) {
      str = JSON.parse(str);
      return jsyaml.safeDump(str);
    }
    return str;
  }

  const podSpecValue = sanitizeVars(EditContainerGroupDataset.data.pod_spec_override);
  const defaultPodSpecValue = canEdit ? sanitizeVars(instanceGroup.model.OPTIONS.actions.PUT.pod_spec_override.default) : '---';

  if ((podSpecValue !== '---') && podSpecValue && podSpecValue.trim() !== defaultPodSpecValue.trim()) {
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
    if (!vm.form.extraVars.isOpen) {
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
