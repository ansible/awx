import React, { useEffect, useCallback } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import { useLocation } from 'react-router-dom';
import { func, shape, arrayOf } from 'prop-types';
import { Form } from '@patternfly/react-core';
import { InstanceGroup } from 'types';
import { VariablesField } from 'components/CodeEditor';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import FormActionGroup from 'components/FormActionGroup';
import FormField, { FormSubmitError } from 'components/FormField';
import { FormColumnLayout, FormFullWidthLayout } from 'components/FormLayout';
import {
  toHostFilter,
  toSearchParams,
} from 'components/Lookup/shared/HostFilterUtils';
import HostFilterLookup from 'components/Lookup/HostFilterLookup';
import InstanceGroupsLookup from 'components/Lookup/InstanceGroupsLookup';
import OrganizationLookup from 'components/Lookup/OrganizationLookup';
import useRequest from 'hooks/useRequest';
import { required } from 'util/validators';
import { InventoriesAPI } from 'api';

const SmartInventoryFormFields = ({ inventory }) => {
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [organizationField, organizationMeta, organizationHelpers] =
    useField('organization');
  const [instanceGroupsField, , instanceGroupsHelpers] =
    useField('instance_groups');
  const [hostFilterField, hostFilterMeta, hostFilterHelpers] = useField({
    name: 'host_filter',
    validate: required(null),
  });
  const handleOrganizationUpdate = useCallback(
    (value) => {
      setFieldValue('organization', value);
      setFieldTouched('organization', true, false);
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
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={handleOrganizationUpdate}
        value={organizationField.value}
        required
        autoPopulate={!inventory?.id}
        validate={required(t`Select a value for this field`)}
      />
      <HostFilterLookup
        value={hostFilterField.value}
        organizationId={organizationField.value?.id}
        helperTextInvalid={hostFilterMeta.error}
        onChange={(value) => {
          hostFilterHelpers.setValue(value);
        }}
        onBlur={() => hostFilterHelpers.setTouched()}
        isValid={!hostFilterMeta.touched || !hostFilterMeta.error}
        isDisabled={!organizationField.value}
        enableNegativeFiltering={false}
        enableRelatedFuzzyFiltering={false}
      />
      <InstanceGroupsLookup
        value={instanceGroupsField.value}
        onChange={(value) => {
          instanceGroupsHelpers.setValue(value);
        }}
        tooltip={t`Select the Instance Groups for this Inventory to run on.`}
      />
      <FormFullWidthLayout>
        <VariablesField
          id="variables"
          name="variables"
          label={t`Variables`}
          tooltip={t`Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Controller documentation for example syntax.`}
        />
      </FormFullWidthLayout>
    </>
  );
};

function SmartInventoryForm({
  inventory,
  instanceGroups,
  onSubmit,
  onCancel,
  submitError,
}) {
  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const hostFilterFromParams = queryParams.get('host_filter');

  function addHostFilter(string) {
    if (!string) return null;
    if (string.includes('ansible_facts') && !string.includes('host_filter')) {
      return string.replace('ansible_facts', 'host_filter=ansible_facts');
    }
    return string;
  }

  const initialValues = {
    description: inventory.description || '',
    host_filter:
      addHostFilter(inventory.host_filter) ||
      (hostFilterFromParams
        ? toHostFilter(toSearchParams(hostFilterFromParams))
        : ''),
    instance_groups: instanceGroups || [],
    kind: 'smart',
    name: inventory.name || '',
    organization: inventory.summary_fields?.organization || null,
    variables: inventory.variables || '---',
  };

  const {
    isLoading,
    error: optionsError,
    request: fetchOptions,
    result: options,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InventoriesAPI.readOptions();
      return data;
    }, []),
    null
  );

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (optionsError) {
    return <ContentError error={optionsError} />;
  }

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values) => {
        onSubmit(values);
      }}
    >
      {(formik) => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <SmartInventoryFormFields inventory={inventory} />
            {submitError && <FormSubmitError error={submitError} />}
            <FormActionGroup
              onCancel={onCancel}
              onSubmit={formik.handleSubmit}
              submitDisabled={!options?.actions?.POST}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}

SmartInventoryForm.propTypes = {
  instanceGroups: arrayOf(InstanceGroup),
  inventory: shape({}),
  onCancel: func.isRequired,
  onSubmit: func.isRequired,
  submitError: shape({}),
};

SmartInventoryForm.defaultProps = {
  instanceGroups: [],
  inventory: {},
  submitError: null,
};

export default SmartInventoryForm;
