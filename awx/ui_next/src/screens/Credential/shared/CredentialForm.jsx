import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { shape } from 'prop-types';
import { Formik, useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
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
import FormField, { FormSubmitError } from '../../../components/FormField';
import {
  FormColumnLayout,
  FormFullWidthLayout,
} from '../../../components/FormLayout';
import { required } from '../../../util/validators';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import TypeInputsSubForm from './TypeInputsSubForm';
import ExternalTestModal from './ExternalTestModal';

const Select = styled(PFSelect)`
  ul {
    max-width: 495px;
  }
  ${props => (props.isDisabled ? `cursor: not-allowed` : null)}
`;

const SelectOption = styled(PFSelectOption)`
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
`;

function CredentialFormFields({ i18n, initialTypeId, credentialTypes }) {
  const { pathname } = useLocation();
  const { setFieldValue, initialValues, setFieldTouched } = useFormikContext();
  const [isSelectOpen, setIsSelectOpen] = useState(false);
  const [credTypeField, credTypeMeta, credTypeHelpers] = useField({
    name: 'credential_type',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const [credentialTypeId, setCredentialTypeId] = useState(initialTypeId);

  const isGalaxyCredential =
    !!credentialTypeId && credentialTypes[credentialTypeId]?.kind === 'galaxy';

  const [orgField, orgMeta, orgHelpers] = useField({
    name: 'organization',
    validate:
      isGalaxyCredential &&
      required(
        i18n._(t`Galaxy credentials must be owned by an Organization.`),
        i18n
      ),
  });

  const credentialTypeOptions = Object.keys(credentialTypes)
    .map(key => {
      return {
        value: credentialTypes[key].id,
        key: credentialTypes[key].id,
        label: credentialTypes[key].name,
      };
    })
    .sort((a, b) => (a.label.toLowerCase() > b.label.toLowerCase() ? 1 : -1));

  const resetSubFormFields = useCallback(
    newCredentialTypeId => {
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

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value);
    },
    [setFieldValue]
  );

  const isCredentialTypeDisabled = pathname.includes('edit');
  const credentialTypeSelect = (
    <Select
      isDisabled={isCredentialTypeDisabled}
      ouiaId="CredentialForm-credential_type"
      aria-label={i18n._(t`Credential Type`)}
      isOpen={isSelectOpen}
      variant={SelectVariant.typeahead}
      onToggle={setIsSelectOpen}
      onSelect={(event, value) => {
        setCredentialTypeId(value);
        credTypeHelpers.setValue(value);
        setIsSelectOpen(false);
      }}
      selections={credTypeField.value}
      placeholder={i18n._(t`Select a credential Type`)}
      isCreatable={false}
      maxHeight="300px"
      width="100%"
    >
      {credentialTypeOptions.map(credType => (
        <SelectOption
          key={credType.value}
          value={credType.value}
          dataCy={`${credType.id}-credential-type-select-option`}
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
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="credential-description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={orgMeta.error}
        isValid={!orgMeta.touched || !orgMeta.error}
        onBlur={() => orgHelpers.setTouched()}
        onChange={onOrganizationChange}
        value={orgField.value}
        touched={orgMeta.touched}
        error={orgMeta.error}
        required={isGalaxyCredential}
        isDisabled={initialValues.isOrgLookupDisabled}
      />
      <FormGroup
        fieldId="credential-Type"
        helperTextInvalid={credTypeMeta.error}
        isRequired
        validated={
          !credTypeMeta.touched || !credTypeMeta.error ? 'default' : 'error'
        }
        label={i18n._(t`Credential Type`)}
      >
        {isCredentialTypeDisabled ? (
          <Tooltip
            content={i18n._(
              `You cannot change the credential type of a credential, 
              as it may break the functionality of the resources using it.`
            )}
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
  i18n,
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
    credential_type: credentialTypes[initialTypeId]?.name || '',
    inputs: credential?.inputs || {},
    passwordPrompts: {},
    isOrgLookupDisabled: isOrgLookupDisabled || false,
  };

  Object.values(credentialTypes).forEach(credentialType => {
    const fields = credentialType.inputs.fields || [];
    fields.forEach(
      ({ ask_at_runtime, type, id, choices, default: defaultValue }) => {
        if (credential?.inputs && credential.inputs[id]) {
          if (ask_at_runtime) {
            initialValues.passwordPrompts[id] =
              credential.inputs[id] === 'ASK' || false;
          }
          initialValues.inputs[id] = credential.inputs[id];
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
  });

  Object.values(inputSources).forEach(inputSource => {
    initialValues.inputs[inputSource.input_field_name] = {
      credential: inputSource.summary_fields.source_credential,
      inputs: inputSource.metadata,
    };
  });

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={values => {
        const { credential_type, ...actualValues } = values;
        // credential_type could be the raw id or the displayed name value.
        // If it's the name, replace it with the id before making the request.
        actualValues.credential_type =
          Object.keys(credentialTypes).find(
            key => credentialTypes[key].name === credential_type
          ) || credential_type;
        onSubmit(actualValues);
      }}
    >
      {formik => (
        <>
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormColumnLayout>
              <CredentialFormFields
                initialTypeId={initialTypeId}
                credentialTypes={credentialTypes}
                i18n={i18n}
                {...rest}
              />
              <FormSubmitError error={submitError} />
              <FormFullWidthLayout>
                <ActionGroup>
                  <Button
                    ouiaId="credential-form-save-button"
                    id="credential-form-save-button"
                    aria-label={i18n._(t`Save`)}
                    variant="primary"
                    type="button"
                    onClick={formik.handleSubmit}
                  >
                    {i18n._(t`Save`)}
                  </Button>
                  {formik?.values?.credential_type &&
                    credentialTypes[formik.values.credential_type]?.kind ===
                      'external' && (
                      <Button
                        ouiaId="credential-form-test-button"
                        id="credential-form-test-button"
                        aria-label={i18n._(t`Test`)}
                        variant="secondary"
                        type="button"
                        onClick={() => setShowExternalTestModal(true)}
                        isDisabled={!formik.isValid}
                      >
                        {i18n._(t`Test`)}
                      </Button>
                    )}
                  <Button
                    ouiaId="credential-form-cancel-button"
                    id="credential-form-cancel-button"
                    aria-label={i18n._(t`Cancel`)}
                    variant="link"
                    type="button"
                    onClick={onCancel}
                  >
                    {i18n._(t`Cancel`)}
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

export default withI18n()(CredentialForm);
