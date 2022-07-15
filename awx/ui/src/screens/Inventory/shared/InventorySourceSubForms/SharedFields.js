import React, { useEffect } from 'react';

import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup } from '@patternfly/react-core';
import { minMaxValue, regExp } from 'util/validators';
import AnsibleSelect from 'components/AnsibleSelect';
import { VariablesField } from 'components/CodeEditor';
import FormField, { CheckboxField } from 'components/FormField';
import { FormFullWidthLayout, FormCheckboxLayout } from 'components/FormLayout';
import Popover from 'components/Popover';
import helpText from '../Inventory.helptext';

export const SourceVarsField = ({ popoverContent }) => (
  <FormFullWidthLayout>
    <VariablesField
      id="source_vars"
      name="source_vars"
      label={t`Source variables`}
      tooltip={
        <>
          {popoverContent}
          {helpText.variables()}
        </>
      }
    />
  </FormFullWidthLayout>
);

export const VerbosityField = () => {
  const [field, meta, helpers] = useField('verbosity');
  const isValid = !(meta.touched && meta.error);
  const options = [
    { value: '0', key: '0', label: t`0 (Warning)` },
    { value: '1', key: '1', label: t`1 (Info)` },
    { value: '2', key: '2', label: t`2 (Debug)` },
  ];

  return (
    <FormGroup
      fieldId="verbosity"
      validated={isValid ? 'default' : 'error'}
      label={t`Verbosity`}
      labelIcon={<Popover content={helpText.subFormVerbosityFields} />}
    >
      <AnsibleSelect
        id="verbosity"
        data={options}
        {...field}
        onChange={(event, value) => helpers.setValue(value)}
      />
    </FormGroup>
  );
};

export const OptionsField = () => {
  const [updateOnLaunchField] = useField('update_on_launch');
  const [, , updateCacheTimeoutHelper] = useField('update_cache_timeout');
  const [projectField] = useField('source_project');

  useEffect(() => {
    if (!updateOnLaunchField.value) {
      updateCacheTimeoutHelper.setValue(0);
    }
  }, [updateOnLaunchField.value]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <FormFullWidthLayout>
        <FormGroup fieldId="option-checkboxes" label={t`Update options`}>
          <FormCheckboxLayout>
            <CheckboxField
              id="overwrite"
              name="overwrite"
              label={t`Overwrite`}
              tooltip={helpText.subFormOptions.overwrite}
            />
            <CheckboxField
              id="overwrite_vars"
              name="overwrite_vars"
              label={t`Overwrite variables`}
              tooltip={helpText.subFormOptions.overwriteVariables}
            />
            <CheckboxField
              id="update_on_launch"
              name="update_on_launch"
              label={t`Update on launch`}
              tooltip={helpText.subFormOptions.updateOnLaunch(projectField)}
            />
          </FormCheckboxLayout>
        </FormGroup>
      </FormFullWidthLayout>
      {updateOnLaunchField.value && (
        <FormField
          id="cache-timeout"
          name="update_cache_timeout"
          type="number"
          min="0"
          max="2147483647"
          validate={minMaxValue(0, 2147483647)}
          label={t`Cache timeout (seconds)`}
          tooltip={helpText.cachedTimeOut}
        />
      )}
    </>
  );
};

export const EnabledVarField = () => (
  <FormField
    id="inventory-enabled-var"
    label={t`Enabled Variable`}
    tooltip={helpText.enabledVariableField}
    name="enabled_var"
    type="text"
  />
);

export const EnabledValueField = () => (
  <FormField
    id="inventory-enabled-value"
    label={t`Enabled Value`}
    tooltip={helpText.enabledValue}
    name="enabled_value"
    type="text"
  />
);

export const HostFilterField = () => (
  <FormField
    id="host-filter"
    label={t`Host Filter`}
    tooltip={helpText.hostFilter}
    name="host_filter"
    type="text"
    validate={regExp()}
  />
);
