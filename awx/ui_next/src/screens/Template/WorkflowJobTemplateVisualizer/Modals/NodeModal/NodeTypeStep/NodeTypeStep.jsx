import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Formik, Field } from 'formik';
import { Form, FormGroup, TextInput } from '@patternfly/react-core';
import { Divider } from '@patternfly/react-core/dist/esm/experimental';
import FormRow from '@components/FormRow';
import AnsibleSelect from '@components/AnsibleSelect';
import VerticalSeperator from '@components/VerticalSeparator';

import InventorySourcesList from './InventorySourcesList';
import JobTemplatesList from './JobTemplatesList';
import ProjectsList from './ProjectsList';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';

const TimeoutInput = styled(TextInput)`
  width: 200px;
  :not(:first-of-type) {
    margin-left: 20px;
  }
`;

const TimeoutLabel = styled.p`
  margin-left: 10px;
`;

function NodeTypeStep({
  i18n,
  nodeType = 'job_template',
  updateNodeType,
  nodeResource,
  updateNodeResource,
  name,
  updateName,
  description,
  updateDescription,
  timeout = 0,
  updateTimeout,
}) {
  return (
    <>
      <div css=" display: flex; align-items: center; margin-bottom: 20px;">
        <b>{i18n._(t`Node Type`)}</b>
        <VerticalSeperator />
        <div>
          <AnsibleSelect
            id="nodeResource-select"
            label={i18n._(t`Select a Node Type`)}
            data={[
              {
                key: 'approval',
                value: 'approval',
                label: i18n._(t`Approval`),
                isDisabled: false,
              },
              {
                key: 'inventory_source_sync',
                value: 'inventory_source_sync',
                label: i18n._(t`Inventory Source Sync`),
                isDisabled: false,
              },
              {
                key: 'job_template',
                value: 'job_template',
                label: i18n._(t`Job Template`),
                isDisabled: false,
              },
              {
                key: 'project_sync',
                value: 'project_sync',
                label: i18n._(t`Project Sync`),
                isDisabled: false,
              },
              {
                key: 'workflow_job_template',
                value: 'workflow_job_template',
                label: i18n._(t`Workflow Job Template`),
                isDisabled: false,
              },
            ]}
            value={nodeType}
            onChange={(e, val) => {
              updateNodeType(val);
            }}
          />
        </div>
      </div>
      <Divider component="div" />
      {nodeType === 'job_template' && (
        <JobTemplatesList
          nodeResource={nodeResource}
          updateNodeResource={updateNodeResource}
        />
      )}
      {nodeType === 'project_sync' && (
        <ProjectsList
          nodeResource={nodeResource}
          updateNodeResource={updateNodeResource}
        />
      )}
      {nodeType === 'inventory_source_sync' && (
        <InventorySourcesList
          nodeResource={nodeResource}
          updateNodeResource={updateNodeResource}
        />
      )}
      {nodeType === 'workflow_job_template' && (
        <WorkflowJobTemplatesList
          nodeResource={nodeResource}
          updateNodeResource={updateNodeResource}
        />
      )}
      {nodeType === 'approval' && (
        <Formik
          initialValues={{
            name: name || '',
            description: description || '',
            timeoutMinutes: Math.floor(timeout / 60),
            timeoutSeconds: timeout - Math.floor(timeout / 60) * 60,
          }}
          render={() => (
            <Form css="margin-top: 20px;">
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
                <FormGroup
                  label={i18n._(t`Timeout`)}
                  fieldId="approval-timeout"
                >
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
      )}
    </>
  );
}

export default withI18n()(NodeTypeStep);
