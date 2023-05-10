import React, { useCallback, useEffect } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { func, shape } from 'prop-types';
import { t } from '@lingui/macro';
import { ConstructedInventoriesAPI } from 'api';
import { minMaxValue, required } from 'util/validators';
import useRequest from 'hooks/useRequest';
import { Form, FormGroup } from '@patternfly/react-core';
import { VariablesField } from 'components/CodeEditor';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import FormActionGroup from 'components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from 'components/FormField';
import { FormFullWidthLayout, FormColumnLayout } from 'components/FormLayout';
import InstanceGroupsLookup from 'components/Lookup/InstanceGroupsLookup';
import InventoryLookup from 'components/Lookup/InventoryLookup';
import OrganizationLookup from 'components/Lookup/OrganizationLookup';
import Popover from 'components/Popover';
import { VerbositySelectField } from 'components/VerbositySelectField';

import ConstructedInventoryHint from './ConstructedInventoryHint';
import getInventoryHelpTextStrings from './Inventory.helptext';

const constructedPluginValidator = {
  plugin: required(t`The plugin parameter is required.`),
};

function ConstructedInventoryFormFields({ inventory = {}, options }) {
  const helpText = getInventoryHelpTextStrings();
  const { setFieldValue, setFieldTouched } = useFormikContext();

  const [instanceGroupsField, , instanceGroupsHelpers] =
    useField('instanceGroups');
  const [organizationField, organizationMeta, organizationHelpers] =
    useField('organization');
  const [inputInventoriesField, inputInventoriesMeta, inputInventoriesHelpers] =
    useField({
      name: 'inputInventories',
      validate: (value) => {
        if (value.length === 0) {
          return t`This field must not be blank`;
        }
        return undefined;
      },
    });
  const handleOrganizationUpdate = useCallback(
    (value) => {
      setFieldValue('organization', value);
      setFieldTouched('organization', true, false);
    },
    [setFieldValue, setFieldTouched]
  );
  const handleInputInventoriesUpdate = useCallback(
    (value) => {
      setFieldValue('inputInventories', value);
      setFieldTouched('inputInventories', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <FormField
        id="name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <OrganizationLookup
        autoPopulate={!inventory?.id}
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={handleOrganizationUpdate}
        validate={required(t`Select a value for this field`)}
        value={organizationField.value}
        required
      />
      <InstanceGroupsLookup
        value={instanceGroupsField.value}
        onChange={(value) => {
          instanceGroupsHelpers.setValue(value);
        }}
        tooltip={t`Select the Instance Groups for this Inventory to run on.`}
      />
      <FormGroup
        isRequired
        fieldId="input-inventories-lookup"
        id="input-inventories-lookup"
        helperTextInvalid={inputInventoriesMeta.error}
        label={t`Input Inventories`}
        labelIcon={
          <Popover
            content={t`Select Input Inventories for the constructed inventory plugin.`}
          />
        }
        validated={
          !inputInventoriesMeta.touched || !inputInventoriesMeta.error
            ? 'default'
            : 'error'
        }
      >
        <InventoryLookup
          fieldId="inputInventories"
          error={inputInventoriesMeta.error}
          onBlur={() => inputInventoriesHelpers.setTouched()}
          onChange={handleInputInventoriesUpdate}
          touched={inputInventoriesMeta.touched}
          value={inputInventoriesField.value}
          hideAdvancedInventories
          multiple
          required
        />
      </FormGroup>
      <FormField
        id="cache-timeout"
        label={t`Cache timeout (seconds)`}
        max="2147483647"
        min="0"
        name="update_cache_timeout"
        tooltip={options.update_cache_timeout.help_text}
        type="number"
        validate={minMaxValue(0, 2147483647)}
      />
      <VerbositySelectField
        fieldId="verbosity"
        tooltip={options.verbosity.help_text}
      />
      <FormFullWidthLayout>
        <ConstructedInventoryHint />
      </FormFullWidthLayout>
      <FormField
        id="limit"
        label={t`Limit`}
        name="limit"
        type="text"
        tooltip={options.limit.help_text}
      />
      <FormFullWidthLayout>
        <VariablesField
          id="source_vars"
          name="source_vars"
          label={t`Source vars`}
          tooltip={helpText.constructedInventorySourceVars()}
          validators={constructedPluginValidator}
          isRequired
        />
      </FormFullWidthLayout>
    </>
  );
}

function ConstructedInventoryForm({
  constructedInventory,
  instanceGroups,
  inputInventories,
  onCancel,
  onSubmit,
  submitError,
}) {
  const initialValues = {
    kind: 'constructed',
    description: constructedInventory?.description || '',
    instanceGroups: instanceGroups || [],
    inputInventories: inputInventories || [],
    limit: constructedInventory?.limit || '',
    name: constructedInventory?.name || '',
    organization: constructedInventory?.summary_fields?.organization || null,
    update_cache_timeout: constructedInventory?.update_cache_timeout || 0,
    verbosity: constructedInventory?.verbosity || 0,
    source_vars: constructedInventory?.source_vars || '---',
  };

  const {
    isLoading,
    error,
    request: fetchOptions,
    result: options,
  } = useRequest(
    useCallback(async () => {
      const res = await ConstructedInventoriesAPI.readOptions();
      const { data } = res;
      return data.actions.POST;
    }, []),
    null
  );

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  if (isLoading || (!options && !error)) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <Formik initialValues={initialValues} onSubmit={onSubmit}>
      {(formik) => (
        <Form role="form" autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <ConstructedInventoryFormFields options={options} />
            {submitError && <FormSubmitError error={submitError} />}
            <FormActionGroup
              onCancel={onCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}

ConstructedInventoryForm.propTypes = {
  onCancel: func.isRequired,
  onSubmit: func.isRequired,
  submitError: shape({}),
};

ConstructedInventoryForm.defaultProps = {
  submitError: null,
};

export default ConstructedInventoryForm;
