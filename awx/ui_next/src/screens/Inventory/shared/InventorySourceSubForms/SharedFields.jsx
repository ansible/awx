import React, { useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup } from '@patternfly/react-core';
import { minMaxValue, regExp } from '../../../../util/validators';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import { VariablesField } from '../../../../components/CodeMirrorInput';
import FormField, { CheckboxField } from '../../../../components/FormField';
import {
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '../../../../components/FormLayout';
import Popover from '../../../../components/Popover';

export const SourceVarsField = withI18n()(({ i18n, popoverContent }) => {
  const jsonExample = `
  {
    "somevar": "somevalue"
    "somepassword": "Magic"
  }
`;
  const yamlExample = `
  ---
  somevar: somevalue
  somepassword: magic
`;
  return (
    <FormFullWidthLayout>
      <VariablesField
        id="source_vars"
        name="source_vars"
        label={i18n._(t`Source variables`)}
        tooltip={
          <div>
            {popoverContent}
            <Trans>
              Enter variables using either JSON or YAML syntax. Use the radio
              button to toggle between the two.
            </Trans>
            <br />
            <br />
            <Trans>JSON:</Trans>
            <pre>{jsonExample}</pre>
            <br />
            <Trans>YAML:</Trans>
            <pre>{yamlExample}</pre>
            <br />
            <Trans>
              View JSON examples at{' '}
              <a
                href="http://www.json.org"
                target="_blank"
                rel="noopener noreferrer"
              >
                www.json.org
              </a>
            </Trans>
            <br />
            <Trans>
              View YAML examples at{' '}
              <a
                href="http://docs.ansible.com/YAMLSyntax.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                docs.ansible.com
              </a>
            </Trans>
          </div>
        }
      />
    </FormFullWidthLayout>
  );
});

export const VerbosityField = withI18n()(({ i18n }) => {
  const [field, meta, helpers] = useField('verbosity');
  const isValid = !(meta.touched && meta.error);
  const options = [
    { value: '0', key: '0', label: i18n._(t`0 (Warning)`) },
    { value: '1', key: '1', label: i18n._(t`1 (Info)`) },
    { value: '2', key: '2', label: i18n._(t`2 (Debug)`) },
  ];
  return (
    <FormGroup
      fieldId="verbosity"
      validated={isValid ? 'default' : 'error'}
      label={i18n._(t`Verbosity`)}
      labelIcon={
        <Popover
          content={i18n._(t`Control the level of output Ansible
        will produce for inventory source update jobs.`)}
        />
      }
    >
      <AnsibleSelect
        id="verbosity"
        data={options}
        {...field}
        onChange={(event, value) => helpers.setValue(value)}
      />
    </FormGroup>
  );
});

export const OptionsField = withI18n()(
  ({ i18n, showProjectUpdate = false }) => {
    const [updateOnLaunchField] = useField('update_on_launch');
    const [, , updateCacheTimeoutHelper] = useField('update_cache_timeout');

    useEffect(() => {
      if (!updateOnLaunchField.value) {
        updateCacheTimeoutHelper.setValue(0);
      }
    }, [updateOnLaunchField.value]); // eslint-disable-line react-hooks/exhaustive-deps

    return (
      <>
        <FormFullWidthLayout>
          <FormGroup
            fieldId="option-checkboxes"
            label={i18n._(t`Update options`)}
          >
            <FormCheckboxLayout>
              <CheckboxField
                id="overwrite"
                name="overwrite"
                label={i18n._(t`Overwrite`)}
                tooltip={
                  <>
                    {i18n._(t`If checked, any hosts and groups that were
                  previously present on the external source but are now removed
                  will be removed from the Tower inventory. Hosts and groups
                  that were not managed by the inventory source will be promoted
                  to the next manually created group or if there is no manually
                  created group to promote them into, they will be left in the "all"
                  default group for the inventory.`)}
                    <br />
                    <br />
                    {i18n._(t`When not checked, local child
                  hosts and groups not found on the external source will remain
                  untouched by the inventory update process.`)}
                  </>
                }
              />
              <CheckboxField
                id="overwrite_vars"
                name="overwrite_vars"
                label={i18n._(t`Overwrite variables`)}
                tooltip={
                  <>
                    {i18n._(t`If checked, all variables for child groups
                  and hosts will be removed and replaced by those found
                  on the external source.`)}
                    <br />
                    <br />
                    {i18n._(t`When not checked, a merge will be performed,
                  combining local variables with those found on the
                  external source.`)}
                  </>
                }
              />
              <CheckboxField
                id="update_on_launch"
                name="update_on_launch"
                label={i18n._(t`Update on launch`)}
                tooltip={i18n._(t`Each time a job runs using this inventory,
            refresh the inventory from the selected source before
            executing job tasks.`)}
              />
              {showProjectUpdate && (
                <CheckboxField
                  id="update_on_project_update"
                  name="update_on_project_update"
                  label={i18n._(t`Update on project update`)}
                  tooltip={i18n._(t`After every project update where the SCM revision
              changes, refresh the inventory from the selected source
              before executing job tasks. This is intended for static content,
              like the Ansible inventory .ini file format.`)}
                />
              )}
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
            validate={minMaxValue(0, 2147483647, i18n)}
            label={i18n._(t`Cache timeout (seconds)`)}
            tooltip={i18n._(t`Time in seconds to consider an inventory sync
              to be current. During job runs and callbacks the task system will
              evaluate the timestamp of the latest sync. If it is older than
              Cache Timeout, it is not considered current, and a new
              inventory sync will be performed.`)}
          />
        )}
      </>
    );
  }
);

export const EnabledVarField = withI18n()(({ i18n }) => {
  return (
    <FormField
      id="inventory-enabled-var"
      label={i18n._(t`Enabled Variable`)}
      tooltip={i18n._(t`Retrieve the enabled state from the given dict of host variables.
        The enabled variable may be specified using dot notation, e.g: 'foo.bar'`)}
      name="enabled_var"
      type="text"
    />
  );
});

export const EnabledValueField = withI18n()(({ i18n }) => {
  return (
    <FormField
      id="inventory-enabled-value"
      label={i18n._(t`Enabled Value`)}
      tooltip={i18n._(
        t`This field is ignored unless an Enabled Variable is set. If the enabled variable matches this value, the host will be enabled on import.`
      )}
      name="enabled_value"
      type="text"
    />
  );
});

export const HostFilterField = withI18n()(({ i18n }) => {
  return (
    <FormField
      id="host-filter"
      label={i18n._(t`Host Filter`)}
      tooltip={i18n._(
        t`Regular expression where only matching host names will be imported. The filter is applied as a post-processing step after any inventory plugin filters are applied.`
      )}
      name="host_filter"
      type="text"
      validate={regExp(i18n)}
    />
  );
});
