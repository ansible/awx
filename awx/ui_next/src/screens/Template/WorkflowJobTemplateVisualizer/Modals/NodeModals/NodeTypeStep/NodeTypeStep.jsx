import React from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { func, number, shape, string } from 'prop-types';
import styled from 'styled-components';
import { Formik, Field } from 'formik';
import { Form, FormGroup, TextInput } from '@patternfly/react-core';
import FormRow from '@components/FormRow';
import AnsibleSelect from '@components/AnsibleSelect';
import VerticalSeperator from '@components/VerticalSeparator';
import InventorySourcesList from './InventorySourcesList';
import JobTemplatesList from './JobTemplatesList';
import ProjectsList from './ProjectsList';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';

const Divider = styled.div`
  height: 1px;
  background-color: var(--pf-global--Color--light-300);
  border: 0;
  flex-shrink: 0;
`;

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
  description,
  i18n,
  name,
  nodeResource,
  nodeType,
  timeout,
  onUpdateDescription,
  onUpdateName,
  onUpdateNodeResource,
  onUpdateNodeType,
  onUpdateTimeout,
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
              onUpdateNodeType(val);
            }}
          />
        </div>
      </div>
      <Divider component="div" />
      {nodeType === 'job_template' && (
        <JobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      )}
      {nodeType === 'project_sync' && (
        <ProjectsList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      )}
      {nodeType === 'inventory_source_sync' && (
        <InventorySourcesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      )}
      {nodeType === 'workflow_job_template' && (
        <WorkflowJobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
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
                        isRequired
                        isValid={isValid}
                        label={i18n._(t`Name`)}
                      >
                        <TextInput
                          autoFocus
                          id="approval-name"
                          isRequired
                          isValid={isValid}
                          type="text"
                          {...field}
                          onChange={(value, evt) => {
                            onUpdateName(value);
                            field.onChange(evt);
                          }}
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
                        onChange={(value, evt) => {
                          onUpdateDescription(value);
                          field.onChange(evt);
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
                            onChange={(value, evt) => {
                              if (!value || value === '') {
                                value = 0;
                              }
                              onUpdateTimeout(
                                Number(value) * 60 +
                                  Number(form.values.timeoutSeconds)
                              );
                              field.onChange(evt);
                            }}
                          />
                          <TimeoutLabel>
                            <Trans>min</Trans>
                          </TimeoutLabel>
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
                            onChange={(value, evt) => {
                              if (!value || value === '') {
                                value = 0;
                              }
                              onUpdateTimeout(
                                Number(value) +
                                  Number(form.values.timeoutMinutes) * 60
                              );
                              field.onChange(evt);
                            }}
                          />
                          <TimeoutLabel>
                            <Trans>sec</Trans>
                          </TimeoutLabel>
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

NodeTypeStep.propTypes = {
  description: string,
  name: string,
  nodeResource: shape(),
  nodeType: string,
  timeout: number,
  onUpdateDescription: func.isRequired,
  onUpdateName: func.isRequired,
  onUpdateNodeResource: func.isRequired,
  onUpdateNodeType: func.isRequired,
  onUpdateTimeout: func.isRequired,
};

NodeTypeStep.defaultProps = {
  description: '',
  name: '',
  nodeResource: null,
  nodeType: 'job_template',
  timeout: 0,
};

export default withI18n()(NodeTypeStep);
