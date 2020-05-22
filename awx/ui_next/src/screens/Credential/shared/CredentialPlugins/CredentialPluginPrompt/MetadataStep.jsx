import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField, useFormikContext } from 'formik';
import styled from 'styled-components';
import { Button, Form, FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import { CredentialTypesAPI } from '../../../../../api';
import AnsibleSelect from '../../../../../components/AnsibleSelect';
import ContentError from '../../../../../components/ContentError';
import ContentLoading from '../../../../../components/ContentLoading';
import FormField from '../../../../../components/FormField';
import { FormFullWidthLayout } from '../../../../../components/FormLayout';
import useRequest from '../../../../../util/useRequest';
import { required } from '../../../../../util/validators';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

const TestButton = styled(Button)`
  margin-top: 20px;
`;

function MetadataStep({ i18n }) {
  const form = useFormikContext();
  const [selectedCredential] = useField('credential');
  const [inputValues] = useField('inputs');

  const {
    result: fields,
    error,
    isLoading,
    request: fetchMetadataOptions,
  } = useRequest(
    useCallback(async () => {
      const {
        data: {
          inputs: { required: requiredFields, metadata },
        },
      } = await CredentialTypesAPI.readDetail(
        selectedCredential.value.credential_type ||
          selectedCredential.value.credential_type_id
      );
      metadata.forEach(field => {
        if (inputValues.value[field.id]) {
          form.initialValues.inputs[field.id] = inputValues.value[field.id];
        } else if (field.type === 'string' && field.choices) {
          form.initialValues.inputs[field.id] =
            field.default || field.choices[0];
        } else {
          form.initialValues.inputs[field.id] = '';
        }
        if (requiredFields && requiredFields.includes(field.id)) {
          field.required = true;
        }
      });
      return metadata;
      /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, []),
    []
  );

  useEffect(() => {
    fetchMetadataOptions();
  }, [fetchMetadataOptions]);

  const testMetadata = () => {
    // todo: implement
  };

  if (isLoading) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <>
      {fields.length > 0 && (
        <Form>
          <FormFullWidthLayout>
            {fields.map(field => {
              if (field.type === 'string') {
                if (field.choices) {
                  return (
                    <FormGroup
                      key={field.id}
                      fieldId={`credential-${field.id}`}
                      label={field.label}
                      isRequired={field.required}
                    >
                      {field.help_text && (
                        <Tooltip content={field.help_text} position="right">
                          <QuestionCircleIcon />
                        </Tooltip>
                      )}
                      <AnsibleSelect
                        name={`inputs.${field.id}`}
                        value={form.values.inputs[field.id]}
                        id={`credential-${field.id}`}
                        data={field.choices.map(choice => {
                          return {
                            value: choice,
                            key: choice,
                            label: choice,
                          };
                        })}
                        onChange={(event, value) => {
                          form.setFieldValue(`inputs.${field.id}`, value);
                        }}
                        validate={field.required ? required(null, i18n) : null}
                      />
                    </FormGroup>
                  );
                }

                return (
                  <FormField
                    key={field.id}
                    id={`credential-${field.id}`}
                    label={field.label}
                    tooltip={field.help_text}
                    name={`inputs.${field.id}`}
                    type={field.multiline ? 'textarea' : 'text'}
                    isRequired={field.required}
                    validate={field.required ? required(null, i18n) : null}
                  />
                );
              }

              return null;
            })}
          </FormFullWidthLayout>
        </Form>
      )}
      <Tooltip
        content={i18n._(
          t`Click this button to verify connection to the secret management system using the selected credential and specified inputs.`
        )}
        position="right"
      >
        <TestButton
          variant="primary"
          type="submit"
          onClick={() => testMetadata()}
        >
          {i18n._(t`Test`)}
        </TestButton>
      </Tooltip>
    </>
  );
}

export default withI18n()(MetadataStep);
