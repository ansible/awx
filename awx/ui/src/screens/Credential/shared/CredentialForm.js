import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { shape } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';

import { t } from '@lingui/macro';
import {
  ActionGroup,
  Button,
  Form,
  FormGroup,
  Select as PFSelect,
  SelectOption as PFSelectOption,
  SelectVariant,
  Tooltip,
} from '@patternfly/react-core';
import styled from 'styled-components';
import FormField, { FormSubmitError } from 'components/FormField';
import { FormColumnLayout, FormFullWidthLayout } from 'components/FormLayout';
import { required } from 'util/validators';
import OrganizationLookup from 'components/Lookup/OrganizationLookup';
import TypeInputsSubForm from './TypeInputsSubForm';
import ExternalTestModal from './ExternalTestModal';

const Select = styled(PFSelect)`
  ul {
    max-width: 495px;
  }
  ${(props) => (props.isDisabled ? `cursor: not-allowed` : null)}
`;

const SelectOption = styled(PFSelectOption)`
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
`;

function CredentialFormFields({ initialTypeId, credentialTypes }) {
  const { pathname } = useLocation();
  const { setFieldValue, initialValues, setFieldTouched } = useFormikContext();
  const [isSelectOpen, setIsSelectOpen] = useState(false);
  const [credTypeField, credTypeMeta, credTypeHelpers] = useField({
    name: 'credential_type',
    validate: required(t`Select a value for this field`),
  });

  const [credentialTypeId, setCredentialTypeId] = useState(initialTypeId);

  const isGalaxyCredential =
    !!credentialTypeId && credentialTypes[credentialTypeId]?.kind === 'galaxy';

  const [orgField, orgMeta, orgHelpers] = useField('organization');

  const credentialTypeOptions = Object.keys(credentialTypes)
    .map((key) => ({
      value: credentialTypes[key].id,
      key: credentialTypes[key].id,
      label: credentialTypes[key].name,
    }))
    .sort((a, b) => (a.label.toLowerCase() > b.label.toLowerCase() ? 1 : -1));

  const resetSubFormFields = useCallback(
    (newCredentialTypeId) => {
      const fields = credentialTypes[newCredentialTypeId].inputs.fields || [];
      fields.forEach(
        ({ ask_at_runtime, type, id, choices, default: defaultValue }) => {
          if (parseInt(newCredentialTypeId, 10) === initialTypeId) {
            setFieldValue(`inputs.${id}`, initialValues.inputs[id]);
            if (ask_at_runtime) {
              setFieldValue(
                `passwordPrompts.${id}`,
                initialValues.passwordPrompts[id]
              );
            }
          } else {
            switch (type) {
              case 'string':
                setFieldValue(`inputs.${id}`, defaultValue || '');
                break;
              case 'boolean':
                setFieldValue(`inputs.${id}`, defaultValue || false);
                break;
              default:
                break;
            }

            if (choices) {
              setFieldValue(`inputs.${id}`, defaultValue);
            }

            if (ask_at_runtime) {
              setFieldValue(`passwordPrompts.${id}`, false);
            }
          }
          setFieldTouched(`inputs.${id}`, false);
        }
      );
    },
    [
      credentialTypes,
      initialTypeId,
      initialValues.inputs,
      initialValues.passwordPrompts,
      setFieldTouched,
      setFieldValue,
    ]
  );

  useEffect(() => {
    if (credentialTypeId) {
      resetSubFormFields(credentialTypeId);
    }
  }, [resetSubFormFields, credentialTypeId]);

  const handleOrganizationUpdate = useCallback(
    (value) => {
      setFieldValue('organization', value);
      setFieldTouched('organization', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  const isCredentialTypeDisabled = pathname.includes('edit');
  const credentialTypeSelect = (
    <Select
      isDisabled={isCredentialTypeDisabled}
      ouiaId="CredentialForm-credential_type"
      aria-label={t`Credential Type`}
      typeAheadAriaLabel={t`Select Credential Type`}
      isOpen={isSelectOpen}
      variant={SelectVariant.typeahead}
      onToggle={setIsSelectOpen}
      onSelect={(event, value) => {
        setCredentialTypeId(value);
        credTypeHelpers.setValue(value);
        setIsSelectOpen(false);
      }}
      selections={credTypeField.value}
      placeholder={t`Select a credential Type`}
      isCreatable={false}
      maxHeight="300px"
      width="100%"
      noResultsFoundText={t`No results found`}
    >
      {credentialTypeOptions.map((credType) => (
        <SelectOption
          key={credType.value}
          value={credType.value}
          data-cy={`${credType.id}-credential-type-select-option`}
        >
          {credType.label}
        </SelectOption>
      ))}
    </Select>
  );

  return (
    <>
      <FormField
        id="credential-name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="credential-description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={orgMeta.error}
        isValid={!orgMeta.touched || !orgMeta.error}
        onBlur={() => orgHelpers.setTouched()}
        onChange={handleOrganizationUpdate}
        value={orgField.value}
        touched={orgMeta.touched}
        error={orgMeta.error}
        required={isGalaxyCredential}
        isDisabled={initialValues.isOrgLookupDisabled}
        validate={
          isGalaxyCredential
            ? required(t`Galaxy credentials must be owned by an Organization.`)
            : undefined
        }
      />
      <FormGroup
        fieldId="credential-Type"
        helperTextInvalid={credTypeMeta.error}
        isRequired
        validated={
          !credTypeMeta.touched || !credTypeMeta.error ? 'default' : 'error'
        }
        label={t`Credential Type`}
      >
        {isCredentialTypeDisabled ? (
          <Tooltip
            content={`You cannot change the credential type of a credential,
              as it may break the functionality of the resources using it.`}
          >
            {credentialTypeSelect}
          </Tooltip>
        ) : (
          credentialTypeSelect
        )}
      </FormGroup>
      {credentialTypeId !== undefined &&
        credentialTypeId !== '' &&
        credentialTypes[credentialTypeId]?.inputs?.fields && (
          <TypeInputsSubForm
            credentialType={credentialTypes[credentialTypeId]}
          />
        )}
    </>
  );
}

function CredentialForm({
  credential = {},
  credentialTypes,
  inputSources,
  onSubmit,
  onCancel,
  submitError,
  isOrgLookupDisabled,
  ...rest
}) {
  const initialTypeId = credential?.credential_type;

  const [showExternalTestModal, setShowExternalTestModal] = useState(false);
  const initialValues = {
    name: credential.name || '',
    description: credential.description || '',
    organization: credential?.summary_fields?.organization || null,
    credential_type: credentialTypes[initialTypeId]?.id || '',
    inputs: { ...credential?.inputs },
    passwordPrompts: {},
    isOrgLookupDisabled: isOrgLookupDisabled || false,
  };

  Object.values(credentialTypes).forEach((credentialType) => {
    if (!credential.id || credential.credential_type === credentialType.id) {
      const fields = credentialType.inputs.fields || [];
      fields.forEach(
        ({ ask_at_runtime, type, id, choices, default: defaultValue }) => {
          if (credential?.inputs && id in credential.inputs) {
            if (ask_at_runtime) {
              initialValues.passwordPrompts[id] =
                credential.inputs[id] === 'ASK' || false;
              initialValues.inputs[id] =
                credential.inputs[id] === 'ASK' ? '' : credential.inputs[id];
            } else {
              initialValues.inputs[id] = credential.inputs[id];
            }
          } else {
            switch (type) {
              case 'string':
                initialValues.inputs[id] = defaultValue || '';
                break;
              case 'boolean':
                initialValues.inputs[id] = defaultValue || false;
                break;
              default:
                break;
            }

            if (choices) {
              initialValues.inputs[id] = defaultValue;
            }

            if (ask_at_runtime) {
              initialValues.passwordPrompts[id] = false;
            }
          }
        }
      );
    }
  });

  Object.values(inputSources).forEach((inputSource) => {
    initialValues.inputs[inputSource.input_field_name] = {
      credential: inputSource.summary_fields.source_credential,
      inputs: inputSource.metadata,
    };
  });

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={(values) => {
        const { credential_type, ...actualValues } = values;
        // credential_type could be the raw id or the displayed name value.
        // If it's the name, replace it with the id before making the request.
        actualValues.credential_type =
          Object.keys(credentialTypes).find(
            (key) => credentialTypes[key].name === credential_type
          ) || credential_type;
        onSubmit(actualValues);
      }}
    >
      {(formik) => (
        <>
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormColumnLayout>
              <CredentialFormFields
                initialTypeId={initialTypeId}
                credentialTypes={credentialTypes}
                {...rest}
              />
              <FormSubmitError error={submitError} />
              <FormFullWidthLayout>
                <ActionGroup>
                  <Button
                    ouiaId="credential-form-save-button"
                    id="credential-form-save-button"
                    aria-label={t`Save`}
                    variant="primary"
                    type="button"
                    onClick={formik.handleSubmit}
                  >
                    {t`Save`}
                  </Button>
                  {formik?.values?.credential_type &&
                    credentialTypes[formik.values.credential_type]?.kind ===
                      'external' && (
                      <Button
                        ouiaId="credential-form-test-button"
                        id="credential-form-test-button"
                        aria-label={t`Test`}
                        variant="secondary"
                        type="button"
                        onClick={() => setShowExternalTestModal(true)}
                        isDisabled={!formik.isValid}
                      >
                        {t`Test`}
                      </Button>
                    )}
                  <Button
                    ouiaId="credential-form-cancel-button"
                    id="credential-form-cancel-button"
                    aria-label={t`Cancel`}
                    variant="link"
                    type="button"
                    onClick={onCancel}
                  >
                    {t`Cancel`}
                  </Button>
                </ActionGroup>
              </FormFullWidthLayout>
            </FormColumnLayout>
          </Form>
          {showExternalTestModal && (
            <ExternalTestModal
              credential={credential}
              credentialType={credentialTypes[formik.values.credential_type]}
              credentialFormValues={formik.values}
              onClose={() => setShowExternalTestModal(false)}
            />
          )}
        </>
      )}
    </Formik>
  );
}

CredentialForm.propTypes = {
  credentialTypes: shape({}).isRequired,
  credential: shape({}),
  inputSources: shape({}),
  submitError: shape({}),
};

CredentialForm.defaultProps = {
  credential: {},
  inputSources: {},
  submitError: null,
};

export default CredentialForm;
