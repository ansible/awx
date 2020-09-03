import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { func, number, shape, string } from 'prop-types';
import styled from 'styled-components';
import { Formik, Field } from 'formik';
import { Form, FormGroup, TextInput } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../../../../../../components/FormLayout';
import AnsibleSelect from '../../../../../../components/AnsibleSelect';
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
TimeoutInput.displayName = 'TimeoutInput';

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
      <div css="display: flex; align-items: center; margin-bottom: 20px;">
        <b css="margin-right: 24px">{i18n._(t`Node Type`)}</b>
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
        >
          {() => (
            <Form css="margin-top: 20px;">
              <FormFullWidthLayout>
                <Field name="name">
                  {({ field, form }) => {
                    const isValid =
                      form &&
                      (!form.touched[field.name] || !form.errors[field.name]);

                    return (
                      <FormGroup
                        fieldId="approval-name"
                        isRequired
                        validated={isValid ? 'default' : 'error'}
                        label={i18n._(t`Name`)}
                      >
                        <TextInput
                          autoFocus
                          id="approval-name"
                          isRequired
                          validated={isValid ? 'default' : 'error'}
                          type="text"
                          {...field}
                          onChange={(value, evt) => {
                            onUpdateName(evt.target.value);
                            field.onChange(evt);
                          }}
                        />
                      </FormGroup>
                    );
                  }}
                </Field>
                <Field name="description">
                  {({ field }) => (
                    <FormGroup
                      fieldId="approval-description"
                      label={i18n._(t`Description`)}
                    >
                      <TextInput
                        id="approval-description"
                        type="text"
                        {...field}
                        onChange={(value, evt) => {
                          onUpdateDescription(evt.target.value);
                          field.onChange(evt);
                        }}
                      />
                    </FormGroup>
                  )}
                </Field>
                <FormGroup
                  label={i18n._(t`Timeout`)}
                  fieldId="approval-timeout"
                >
                  <div css="display: flex;align-items: center;">
                    <Field name="timeoutMinutes">
                      {({ field, form }) => (
                        <>
                          <TimeoutInput
                            id="approval-timeout-minutes"
                            type="number"
                            min="0"
                            step="1"
                            {...field}
                            onChange={(value, evt) => {
                              if (
                                !evt.target.value ||
                                evt.target.value === ''
                              ) {
                                evt.target.value = 0;
                              }
                              onUpdateTimeout(
                                Number(evt.target.value) * 60 +
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
                    </Field>
                    <Field name="timeoutSeconds">
                      {({ field, form }) => (
                        <>
                          <TimeoutInput
                            id="approval-timeout-seconds"
                            type="number"
                            min="0"
                            step="1"
                            {...field}
                            onChange={(value, evt) => {
                              if (
                                !evt.target.value ||
                                evt.target.value === ''
                              ) {
                                evt.target.value = 0;
                              }
                              onUpdateTimeout(
                                Number(evt.target.value) +
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
                    </Field>
                  </div>
                </FormGroup>
              </FormFullWidthLayout>
            </Form>
          )}
        </Formik>
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
