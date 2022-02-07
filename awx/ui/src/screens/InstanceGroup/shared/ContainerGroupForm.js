import React, { useCallback } from 'react';
import { func, shape } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';

import { t } from '@lingui/macro';
import { Form, FormGroup } from '@patternfly/react-core';
import { jsonToYaml } from 'util/yaml';

import FormField, {
  FormSubmitError,
  CheckboxField,
} from 'components/FormField';
import FormActionGroup from 'components/FormActionGroup';
import { combine, required, protectedResourceName } from 'util/validators';
import {
  FormColumnLayout,
  FormFullWidthLayout,
  FormCheckboxLayout,
  SubFormLayout,
} from 'components/FormLayout';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import { VariablesField } from 'components/CodeEditor';

function ContainerGroupFormFields({
  instanceGroup,
  defaultControlPlane,
  defaultExecution,
}) {
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [credentialField, credentialMeta, credentialHelpers] =
    useField('credential');

  const [, { initialValue }] = useField('name');

  const isProtected =
    initialValue === `${defaultControlPlane}` ||
    initialValue === `${defaultExecution}`;

  const [overrideField] = useField('override');

  const handleCredentialUpdate = useCallback(
    (value) => {
      setFieldValue('credential', value);
      setFieldTouched('credential', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <FormField
        name="name"
        helperText={
          isProtected
            ? t`This is a protected Instance Group. The name cannot be changed.`
            : ''
        }
        id="container-group-name"
        label={t`Name`}
        type="text"
        validate={combine([
          required(null),
          protectedResourceName(
            t`This is a protected name for Container Groups. Please use a different name.`,
            [defaultControlPlane, defaultExecution]
          ),
        ])}
        isRequired
      />
      <CredentialLookup
        label={t`Credential`}
        credentialTypeKind="kubernetes"
        helperTextInvalid={credentialMeta.error}
        isValid={!credentialMeta.touched || !credentialMeta.error}
        onBlur={() => credentialHelpers.setTouched()}
        onChange={handleCredentialUpdate}
        value={credentialField.value}
        tooltip={t`Credential to authenticate with Kubernetes or OpenShift. Must be of type "Kubernetes/OpenShift API Bearer Token". If left blank, the underlying Pod's service account will be used.`}
        autoPopulate={!instanceGroup?.id}
      />

      <FormGroup fieldId="container-groups-option-checkbox" label={t`Options`}>
        <FormCheckboxLayout>
          <CheckboxField
            name="override"
            aria-label={t`Customize pod specification`}
            label={t`Customize pod specification`}
            id="container-groups-override-pod-specification"
          />
        </FormCheckboxLayout>
      </FormGroup>

      {overrideField.value && (
        <SubFormLayout>
          <FormFullWidthLayout>
            <VariablesField
              tooltip={t`Field for passing a custom Kubernetes or OpenShift Pod specification.`}
              id="custom-pod-spec"
              name="pod_spec_override"
              label={t`Custom pod spec`}
            />
          </FormFullWidthLayout>
        </SubFormLayout>
      )}
    </>
  );
}

function ContainerGroupForm({
  initialPodSpec,
  instanceGroup,
  onSubmit,
  onCancel,
  submitError,
  ...rest
}) {
  const isCheckboxChecked = Boolean(instanceGroup?.pod_spec_override) || false;

  const initialValues = {
    name: instanceGroup?.name || '',
    credential: instanceGroup?.summary_fields?.credential,
    pod_spec_override: isCheckboxChecked
      ? instanceGroup?.pod_spec_override
      : jsonToYaml(JSON.stringify(initialPodSpec)),
    override: isCheckboxChecked,
  };

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
            <ContainerGroupFormFields instanceGroup={instanceGroup} {...rest} />
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

ContainerGroupForm.propTypes = {
  instanceGroup: shape({}),
  onCancel: func.isRequired,
  onSubmit: func.isRequired,
  submitError: shape({}),
  initialPodSpec: shape({}),
};

ContainerGroupForm.defaultProps = {
  instanceGroup: {},
  submitError: null,
  initialPodSpec: {},
};

export default ContainerGroupForm;
