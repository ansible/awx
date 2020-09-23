import React, { useEffect, useCallback } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape, object, arrayOf } from 'prop-types';
import { Form } from '@patternfly/react-core';
import { VariablesField } from '../../../components/CodeMirrorInput';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import FormActionGroup from '../../../components/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
} from '../../../components/FormLayout';
import HostFilterLookup from '../../../components/Lookup/HostFilterLookup';
import InstanceGroupsLookup from '../../../components/Lookup/InstanceGroupsLookup';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import useRequest from '../../../util/useRequest';
import { required } from '../../../util/validators';
import { InventoriesAPI } from '../../../api';

const SmartInventoryFormFields = withI18n()(({ i18n, inventory }) => {
  const { setFieldValue } = useFormikContext();
  const [organizationField, organizationMeta, organizationHelpers] = useField({
    name: 'organization',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [instanceGroupsField, , instanceGroupsHelpers] = useField({
    name: 'instance_groups',
  });
  const [hostFilterField, hostFilterMeta, hostFilterHelpers] = useField({
    name: 'host_filter',
    validate: required(null, i18n),
  });
  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={organizationMeta.error}
        isValid={!organizationMeta.touched || !organizationMeta.error}
        onBlur={() => organizationHelpers.setTouched()}
        onChange={onOrganizationChange}
        value={organizationField.value}
        required
        autoPopulate={!inventory?.id}
      />
      <HostFilterLookup
        value={hostFilterField.value}
        organizationId={organizationField.value?.id}
        helperTextInvalid={hostFilterMeta.error}
        onChange={value => {
          hostFilterHelpers.setValue(value);
        }}
        onBlur={() => hostFilterHelpers.setTouched()}
        isValid={!hostFilterMeta.touched || !hostFilterMeta.error}
        isDisabled={!organizationField.value}
      />
      <InstanceGroupsLookup
        value={instanceGroupsField.value}
        onChange={value => {
          instanceGroupsHelpers.setValue(value);
        }}
      />
      <FormFullWidthLayout>
        <VariablesField
          id="variables"
          name="variables"
          label={i18n._(t`Variables`)}
          tooltip={i18n._(
            t`Enter inventory variables using either JSON or YAML syntax.
            Use the radio button to toggle between the two. Refer to the
            Ansible Tower documentation for example syntax.`
          )}
        />
      </FormFullWidthLayout>
    </>
  );
});

function SmartInventoryForm({
  inventory,
  instanceGroups,
  onSubmit,
  onCancel,
  submitError,
}) {
  const initialValues = {
    description: inventory.description || '',
    host_filter: inventory.host_filter || '',
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
      onSubmit={values => {
        onSubmit(values);
      }}
    >
      {formik => (
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
  instanceGroups: arrayOf(object),
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

export default withI18n()(SmartInventoryForm);
