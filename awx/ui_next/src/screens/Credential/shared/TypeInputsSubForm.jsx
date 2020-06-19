import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Title } from '@patternfly/react-core';
import {
  FormCheckboxLayout,
  FormColumnLayout,
  FormFullWidthLayout,
  SubFormLayout,
} from '../../../components/FormLayout';
import { CheckboxField } from '../../../components/FormField';
import { CredentialType } from '../../../types';
import { CredentialField, GceFileUploadField } from './CredentialFormFields';

function TypeInputsSubForm({ credentialType, i18n }) {
  const stringFields = credentialType.inputs.fields.filter(
    fieldOptions => fieldOptions.type === 'string' || fieldOptions.choices
  );
  const booleanFields = credentialType.inputs.fields.filter(
    fieldOptions => fieldOptions.type === 'boolean'
  );
  return (
    <SubFormLayout>
      <Title size="md" headingLevel="h4">
        {i18n._(t`Type Details`)}
      </Title>
      <FormColumnLayout>
        {credentialType.namespace === 'gce' && <GceFileUploadField />}
        {stringFields.map(fieldOptions =>
          fieldOptions.multiline ? (
            <FormFullWidthLayout key={fieldOptions.id}>
              <CredentialField
                credentialType={credentialType}
                fieldOptions={fieldOptions}
              />
            </FormFullWidthLayout>
          ) : (
            <CredentialField
              key={fieldOptions.id}
              credentialType={credentialType}
              fieldOptions={fieldOptions}
            />
          )
        )}
        {booleanFields.length > 0 && (
          <FormFullWidthLayout>
            <FormGroup
              fieldId="credential-checkboxes"
              label={i18n._(t`Options`)}
            >
              <FormCheckboxLayout>
                {booleanFields.map(fieldOptions => (
                  <CheckboxField
                    id={`credential-${fieldOptions.id}`}
                    key={fieldOptions.id}
                    name={`inputs.${fieldOptions.id}`}
                    label={fieldOptions.label}
                    tooltip={fieldOptions.help_text}
                  />
                ))}
              </FormCheckboxLayout>
            </FormGroup>
          </FormFullWidthLayout>
        )}
      </FormColumnLayout>
    </SubFormLayout>
  );
}

TypeInputsSubForm.propTypes = {
  credentialType: CredentialType.isRequired,
};

TypeInputsSubForm.defaultProps = {};

export default withI18n()(TypeInputsSubForm);
