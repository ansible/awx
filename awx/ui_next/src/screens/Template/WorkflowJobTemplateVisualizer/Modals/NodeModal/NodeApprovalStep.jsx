import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Formik, Field } from 'formik';
import { Form, FormGroup, TextInput, Title } from '@patternfly/react-core';
import FormRow from '@components/FormRow';
import HorizontalSeparator from '@components/HorizontalSeparator';

const TimeoutInput = styled(TextInput)`
  width: 200px;
  :not(:first-of-type) {
    margin-left: 20px;
  }
`;

const TimeoutLabel = styled.p`
  margin-left: 10px;
`;

function NodeApprovalStep({
  i18n,
  name,
  updateName,
  description,
  updateDescription,
  timeout = 0,
  updateTimeout,
}) {
  return (
    <div>
      <Title headingLevel="h1" size="xl">
        {i18n._(t`Approval Node`)}
      </Title>
      <HorizontalSeparator />
      <Formik
        initialValues={{
          name: name || '',
          description: description || '',
          timeoutMinutes: Math.floor(timeout / 60),
          timeoutSeconds: timeout - Math.floor(timeout / 60) * 60,
        }}
        render={() => (
          <Form>
            <FormRow>
              <Field
                name="name"
                render={({ field, form }) => {
                  const isValid =
                    form &&
                    (!form.touched[field.name] || !form.errors[field.name]);

                  return (
                    <FormGroup
                      fieldId="approval-name"
                      isRequired={true}
                      isValid={isValid}
                      label={i18n._(t`Name`)}
                    >
                      <TextInput
                        id="approval-name"
                        isRequired={true}
                        isValid={isValid}
                        type="text"
                        {...field}
                        onChange={(value, event) => {
                          updateName(value);
                          field.onChange(event);
                        }}
                        autoFocus
                      />
                    </FormGroup>
                  );
                }}
              />
            </FormRow>
            <FormRow>
              <Field
                name="description"
                render={({ field }) => (
                  <FormGroup
                    fieldId="approval-description"
                    label={i18n._(t`Description`)}
                  >
                    <TextInput
                      id="approval-description"
                      type="text"
                      {...field}
                      onChange={value => {
                        updateDescription(value);
                        field.onChange(event);
                      }}
                    />
                  </FormGroup>
                )}
              />
            </FormRow>
            <FormRow>
              <FormGroup label={i18n._(t`Timeout`)} fieldId="approval-timeout">
                <div css="display: flex;align-items: center;">
                  <Field
                    name="timeoutMinutes"
                    render={({ field, form }) => (
                      <>
                        <TimeoutInput
                          id="approval-timeout-minutes"
                          type="number"
                          min="0"
                          step="1"
                          {...field}
                          onChange={value => {
                            if (!value || value === '') {
                              value = 0;
                            }
                            updateTimeout(
                              Number(value) * 60 +
                                Number(form.values.timeoutSeconds)
                            );
                            field.onChange(event);
                          }}
                        />
                        <TimeoutLabel>min</TimeoutLabel>
                      </>
                    )}
                  />
                  <Field
                    name="timeoutSeconds"
                    render={({ field, form }) => (
                      <>
                        <TimeoutInput
                          id="approval-timeout-seconds"
                          type="number"
                          min="0"
                          step="1"
                          {...field}
                          onChange={value => {
                            if (!value || value === '') {
                              value = 0;
                            }
                            updateTimeout(
                              Number(value) +
                                Number(form.values.timeoutMinutes) * 60
                            );
                            field.onChange(event);
                          }}
                        />
                        <TimeoutLabel>sec</TimeoutLabel>
                      </>
                    )}
                  />
                </div>
              </FormGroup>
            </FormRow>
          </Form>
        )}
      />
    </div>
  );
}

export default withI18n()(NodeApprovalStep);
