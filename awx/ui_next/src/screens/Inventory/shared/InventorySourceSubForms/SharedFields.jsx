import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { useField } from 'formik';
import {
  FormGroup,
  Select,
  SelectOption,
  SelectVariant,
} from '@patternfly/react-core';
import { arrayToString, stringToArray } from '../../../../util/strings';
import { minMaxValue } from '../../../../util/validators';
import { BrandName } from '../../../../variables';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import { VariablesField } from '../../../../components/CodeMirrorInput';
import FormField, {
  CheckboxField,
  FieldTooltip,
} from '../../../../components/FormField';
import {
  FormFullWidthLayout,
  FormCheckboxLayout,
} from '../../../../components/FormLayout';

export const SourceVarsField = withI18n()(({ i18n }) => (
  <FormFullWidthLayout>
    <VariablesField
      id="source_vars"
      name="source_vars"
      label={i18n._(t`Source variables`)}
    />
  </FormFullWidthLayout>
));

export const RegionsField = withI18n()(({ i18n, regionOptions }) => {
  const [field, meta, helpers] = useField('source_regions');
  const [isOpen, setIsOpen] = useState(false);
  const options = Object.assign(
    {},
    ...regionOptions.map(([key, val]) => ({ [key]: val }))
  );
  const selected = stringToArray(field?.value)
    .filter(i => options[i])
    .map(val => options[val]);

  return (
    <FormGroup
      fieldId="regions"
      helperTextInvalid={meta.error}
      validated="default"
      label={i18n._(t`Regions`)}
    >
      <FieldTooltip
        content={
          <Trans>
            Click on the regions field to see a list of regions for your cloud
            provider. You can select multiple regions, or choose
            <em> All</em> to include all regions. Only Hosts associated with the
            selected regions will be updated.
          </Trans>
        }
      />
      <Select
        variant={SelectVariant.typeaheadMulti}
        id="regions"
        onToggle={setIsOpen}
        onClear={() => helpers.setValue('')}
        onSelect={(event, option) => {
          let selectedValues;
          if (selected.includes(option)) {
            selectedValues = selected.filter(o => o !== option);
          } else {
            selectedValues = selected.concat(option);
          }
          const selectedKeys = selectedValues.map(val =>
            Object.keys(options).find(key => options[key] === val)
          );
          helpers.setValue(arrayToString(selectedKeys));
        }}
        isExpanded={isOpen}
        placeholderText={i18n._(t`Select a region`)}
        selections={selected}
      >
        {regionOptions.map(([key, val]) => (
          <SelectOption key={key} value={val} />
        ))}
      </Select>
    </FormGroup>
  );
});

export const GroupByField = withI18n()(
  ({ i18n, fixedOptions, isCreatable = false }) => {
    const [field, meta, helpers] = useField('group_by');
    const fixedOptionLabels = fixedOptions && Object.values(fixedOptions);
    const selections = fixedOptions
      ? stringToArray(field.value).map(o => fixedOptions[o])
      : stringToArray(field.value);
    const [options, setOptions] = useState(selections);
    const [isOpen, setIsOpen] = useState(false);

    const renderOptions = opts => {
      return opts.map(option => (
        <SelectOption key={option} value={option}>
          {option}
        </SelectOption>
      ));
    };

    const handleFilter = event => {
      const str = event.target.value.toLowerCase();
      let matches;
      if (fixedOptions) {
        matches = fixedOptionLabels.filter(o => o.toLowerCase().includes(str));
      } else {
        matches = options.filter(o => o.toLowerCase().includes(str));
      }
      return renderOptions(matches);
    };

    const handleSelect = (e, option) => {
      let selectedValues;
      if (selections.includes(option)) {
        selectedValues = selections.filter(o => o !== option);
      } else {
        selectedValues = selections.concat(option);
      }
      if (fixedOptions) {
        selectedValues = selectedValues.map(val =>
          Object.keys(fixedOptions).find(key => fixedOptions[key] === val)
        );
      }
      helpers.setValue(arrayToString(selectedValues));
    };

    return (
      <FormGroup
        fieldId="group-by"
        helperTextInvalid={meta.error}
        validated="default"
        label={i18n._(t`Only group by`)}
      >
        <FieldTooltip
          content={
            <Trans>
              Select which groups to create automatically. AWX will create group
              names similar to the following examples based on the options
              selected:
              <br />
              <br />
              <ul>
                <li>
                  Availability Zone: <strong>zones &raquo; us-east-1b</strong>
                </li>
                <li>
                  Image ID: <strong>images &raquo; ami-b007ab1e</strong>
                </li>
                <li>
                  Instance ID: <strong>instances &raquo; i-ca11ab1e </strong>
                </li>
                <li>
                  Instance Type: <strong>types &raquo; type_m1_medium</strong>
                </li>
                <li>
                  Key Name: <strong>keys &raquo; key_testing</strong>
                </li>
                <li>
                  Region: <strong>regions &raquo; us-east-1</strong>
                </li>
                <li>
                  Security Group:{' '}
                  <strong>
                    security_groups &raquo; security_group_default
                  </strong>
                </li>
                <li>
                  Tags: <strong>tags &raquo; tag_Name_host1</strong>
                </li>
                <li>
                  VPC ID: <strong>vpcs &raquo; vpc-5ca1ab1e</strong>
                </li>
                <li>
                  Tag None: <strong>tags &raquo; tag_none</strong>
                </li>
              </ul>
              <br />
              If blank, all groups above are created except <em>Instance ID</em>
              .
            </Trans>
          }
        />
        <Select
          variant={SelectVariant.typeaheadMulti}
          id="group-by"
          onToggle={setIsOpen}
          onClear={() => helpers.setValue('')}
          isCreatable={isCreatable}
          createText={i18n._(t`Create`)}
          onCreateOption={name => {
            name = name.trim();
            if (!options.find(opt => opt === name)) {
              setOptions(options.concat(name));
            }
            return name;
          }}
          onFilter={handleFilter}
          onSelect={handleSelect}
          isExpanded={isOpen}
          placeholderText={i18n._(t`Select a group`)}
          selections={selections}
        >
          {fixedOptions
            ? renderOptions(fixedOptionLabels)
            : renderOptions(options)}
        </Select>
      </FormGroup>
    );
  }
);

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
      validated={(isValid) ? 'default' : 'error'}
      label={i18n._(t`Verbosity`)}
    >
      <FieldTooltip
        content={i18n._(t`Control the level of output Ansible
        will produce for inventory source update jobs.`)}
      />
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

export const InstanceFiltersField = withI18n()(({ i18n }) => {
  // Setting BrandName to a variable here is necessary to get the jest tests
  // passing.  Attempting to use BrandName in the template literal results
  // in failing tests.
  const brandName = BrandName;
  return (
    <FormField
      id="instance-filters"
      label={i18n._(t`Instance filters`)}
      name="instance_filters"
      type="text"
      tooltip={
        <Trans>
          Provide a comma-separated list of filter expressions. Hosts are
          imported to {brandName} when <em>ANY</em> of the filters match.
          <br />
          <br />
          Limit to hosts having a tag:
          <br />
          tag-key=TowerManaged
          <br />
          <br />
          Limit to hosts using either key pair:
          <br />
          key-name=staging, key-name=production
          <br />
          <br />
          Limit to hosts where the Name tag begins with <em>test</em>:<br />
          tag:Name=test*
          <br />
          <br />
          View the
          <a
            href="http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-DescribeInstances.html\"
            target="_blank\"
          >
            {' '}
            Describe Instances documentation{' '}
          </a>
          for a complete list of supported filters.
        </Trans>
      }
    />
  );
});
