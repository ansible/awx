import React from 'react';
import { Wizard } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import InventoryStep from './InventoryStep';
import CredentialsStep from './CredentialsStep';
import OtherPromptsStep from './OtherPromptsStep';
import SurveyStep from './SurveyStep';
import PreviewStep from './PreviewStep';

function LaunchPrompt({ config, i18n }) {
  // can_start_without_user_input: false
  // passwords_needed_to_start: []
  // ask_scm_branch_on_launch: false
  // ask_variables_on_launch: true
  // ask_tags_on_launch: false
  // ask_diff_mode_on_launch: false
  // ask_skip_tags_on_launch: false
  // ask_job_type_on_launch: false
  // ask_limit_on_launch: false
  // ask_verbosity_on_launch: false
  // ask_inventory_on_launch: false
  // ask_credential_on_launch: true
  // survey_enabled: false
  // variables_needed_to_start: []
  // credential_needed_to_start: false
  // inventory_needed_to_start: false
  // job_template_data: {name: "JT with prompts", id: 25, description: ""
  const steps = [];
  if (config.ask_inventory_on_launch) {
    steps.push({
      name: i18n._(t`Inventory`),
      component: <InventoryStep />,
    });
  }
  // angular code was:
  // if (vm.promptDataClone.launchConf.ask_credential_on_launch ||
  //     (_.has(vm, 'promptDataClone.prompts.credentials.passwords.vault') &&
  //     vm.promptDataClone.prompts.credentials.passwords.vault.length > 0) ||
  //     _.has(vm, 'promptDataClone.prompts.credentials.passwords.ssh_key_unlock') ||
  //     _.has(vm, 'promptDataClone.prompts.credentials.passwords.become_password') ||
  //     _.has(vm, 'promptDataClone.prompts.credentials.passwords.ssh_password')
  // ) {
  if (config.ask_credential_on_launch) {
    steps.push({
      name: i18n._(t`Credential`),
      component: <CredentialsStep />,
    });
  }
  if (
    config.ask_scm_branch_on_launch ||
    (config.ask_variables_on_launch && !config.ignore_ask_variables) ||
    config.ask_tags_on_launch ||
    config.ask_diff_mode_on_launch ||
    config.ask_skip_tags_on_launch ||
    config.ask_job_type_on_launch ||
    config.ask_limit_on_launch ||
    config.ask_verbosity_on_launch
  ) {
    steps.push({
      name: i18n._(t`Other Prompts`),
      component: <OtherPromptsStep config={config} />,
    });
  }
  if (config.survey_enabled) {
    steps.push({
      name: i18n._(t`Survey`),
      component: <SurveyStep />,
    });
  }
  steps.push({
    name: i18n._(t`Preview`),
    component: <PreviewStep />,
  });

  const handleClose = x => {
    console.log(x);
  };

  return (
    <Wizard
      isOpen
      onClose={handleClose}
      title={i18n._(t`Prompts`)}
      steps={steps}
    />
  );
}

export default withI18n()(LaunchPrompt);
