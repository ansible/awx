import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { useField, useFormikContext } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import { CredentialTypesAPI } from '../../../../../api';
import AnsibleSelect from '../../../../../components/AnsibleSelect';
import ContentError from '../../../../../components/ContentError';
import ContentLoading from '../../../../../components/ContentLoading';
import FormField from '../../../../../components/FormField';
import { FormFullWidthLayout } from '../../../../../components/FormLayout';
import Popover from '../../../../../components/Popover';
import useRequest from '../../../../../util/useRequest';
import { required } from '../../../../../util/validators';

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
                      labelIcon={
                        field.help_text && <Popover content={field.help_text} />
                      }
                    >
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
    </>
  );
}

export default withI18n()(MetadataStep);
