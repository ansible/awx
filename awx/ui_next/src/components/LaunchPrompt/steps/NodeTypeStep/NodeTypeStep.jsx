import 'styled-components/macro';
import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import styled from 'styled-components';
import { useField } from 'formik';
import { Form, FormGroup, TextInput } from '@patternfly/react-core';
import { required } from '../../../../util/validators';

import { FormFullWidthLayout } from '../../../FormLayout';
import AnsibleSelect from '../../../AnsibleSelect';
import InventorySourcesList from './InventorySourcesList';
import JobTemplatesList from './JobTemplatesList';
import ProjectsList from './ProjectsList';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';
import FormField from '../../../FormField';

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

function NodeTypeStep({ i18n }) {
  const [timeoutMinutes, setTimeoutMinutes] = useState(0);
  const [timeoutSeconds, setTimeoutSeconds] = useState(0);
  const [nodeTypeField, , nodeTypeHelpers] = useField('nodeType');
  const [nodeResourceField, , nodeResourceHelpers] = useField('nodeResource');
  const [, approvalNameMeta, approvalNameHelpers] = useField('approvalName');
  const [, , approvalDescriptionHelpers] = useField('approvalDescription');
  const [, , timeoutHelpers] = useField('timeout');

  const isValid = !approvalNameMeta.touched || !approvalNameMeta.error;
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
            value={nodeTypeField.value}
            onChange={(e, val) => {
              nodeTypeHelpers.setValue(val);
              nodeResourceHelpers.setValue(null);
              approvalNameHelpers.setValue('');
              approvalDescriptionHelpers.setValue('');
              timeoutHelpers.setValue(0);
            }}
          />
        </div>
      </div>
      {nodeTypeField.value === 'job_template' && (
        <JobTemplatesList
          nodeResource={nodeResourceField.value}
          onUpdateNodeResource={nodeResourceHelpers.setValue}
        />
      )}
      {nodeTypeField.value === 'project_sync' && (
        <ProjectsList
          nodeResource={nodeResourceField.value}
          onUpdateNodeResource={nodeResourceHelpers.setValue}
        />
      )}
      {nodeTypeField.value === 'inventory_source_sync' && (
        <InventorySourcesList
          nodeResource={nodeResourceField.value}
          onUpdateNodeResource={nodeResourceHelpers.setValue}
        />
      )}
      {nodeTypeField.value === 'workflow_job_template' && (
        <WorkflowJobTemplatesList
          nodeResource={nodeResourceField.value}
          onUpdateNodeResource={nodeResourceHelpers.setValue}
        />
      )}
      {nodeTypeField.value === 'approval' && (
        <Form css="margin-top: 20px;">
          <FormFullWidthLayout>
            <FormField
              name="approvalName"
              fieldId="approval-name"
              id="approval-name"
              isRequired
              validate={required(null, i18n)}
              validated={isValid ? 'default' : 'error'}
              label={i18n._(t`Name`)}
            />
            <FormField
              name="approvalDescription"
              fieldId="approval-description"
              id="approval-description"
              label={i18n._(t`Description`)}
            />
            <FormGroup
              label={i18n._(t`Timeout`)}
              fieldId="approval-timeout"
              name="timeout"
            >
              <div css="display: flex;align-items: center;">
                <TimeoutInput
                  aria-label={i18n._(t`timeout-minutes`)}
                  name="timeoutMinutes"
                  id="approval-timeout-minutes"
                  type="number"
                  min="0"
                  step="1"
                  value={timeoutMinutes}
                  onChange={(value, evt) => {
                    if (!evt.target.value || evt.target.value === '') {
                      evt.target.value = 0;
                    }
                    setTimeoutMinutes(evt.target.value);
                    timeoutHelpers.setValue(
                      Number(evt.target.value) * 60 + Number(timeoutSeconds)
                    );
                  }}
                />
                <TimeoutLabel>
                  <Trans>min</Trans>
                </TimeoutLabel>
                <TimeoutInput
                  name="timeoutSeconds"
                  id="approval-timeout-seconds"
                  type="number"
                  aria-label={i18n._(t`timeout-seconds`)}
                  min="0"
                  step="1"
                  value={timeoutSeconds}
                  onChange={(value, evt) => {
                    if (!evt.target.value || evt.target.value === '') {
                      evt.target.value = 0;
                    }
                    setTimeoutSeconds(evt.target.value);

                    timeoutHelpers.setValue(
                      Number(evt.target.value) + Number(timeoutMinutes) * 60
                    );
                  }}
                />
                <TimeoutLabel>
                  <Trans>sec</Trans>
                </TimeoutLabel>
              </div>
            </FormGroup>
          </FormFullWidthLayout>
        </Form>
      )}
    </>
  );
}

export default withI18n()(NodeTypeStep);
