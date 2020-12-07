import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import styled from 'styled-components';
import { useField } from 'formik';
import { Form, FormGroup, TextInput } from '@patternfly/react-core';
import { required } from '../../../../../../util/validators';

import { FormFullWidthLayout } from '../../../../../../components/FormLayout';
import AnsibleSelect from '../../../../../../components/AnsibleSelect';
import InventorySourcesList from './InventorySourcesList';
import JobTemplatesList from './JobTemplatesList';
import ProjectsList from './ProjectsList';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';
import FormField from '../../../../../../components/FormField';

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
  const [nodeTypeField, , nodeTypeHelpers] = useField('nodeType');
  const [nodeResourceField, , nodeResourceHelpers] = useField('nodeResource');
  const [, approvalNameMeta, approvalNameHelpers] = useField('approvalName');
  const [, , approvalDescriptionHelpers] = useField('approvalDescription');
  const [timeoutMinutesField, , timeoutMinutesHelpers] = useField(
    'timeoutMinutes'
  );
  const [timeoutSecondsField, , timeoutSecondsHelpers] = useField(
    'timeoutSeconds'
  );

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
                key: 'workflow_approval_template',
                value: 'workflow_approval_template',
                label: i18n._(t`Approval`),
                isDisabled: false,
              },
              {
                key: 'inventory_source',
                value: 'inventory_source',
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
                key: 'project',
                value: 'project',
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
              timeoutMinutesHelpers.setValue(0);
              timeoutSecondsHelpers.setValue(0);
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
      {nodeTypeField.value === 'project' && (
        <ProjectsList
          nodeResource={nodeResourceField.value}
          onUpdateNodeResource={nodeResourceHelpers.setValue}
        />
      )}
      {nodeTypeField.value === 'inventory_source' && (
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
      {nodeTypeField.value === 'workflow_approval_template' && (
        <Form css="margin-top: 20px;">
          <FormFullWidthLayout>
            <FormField
              name="approvalName"
              id="approval-name"
              isRequired
              validate={required(null, i18n)}
              validated={isValid ? 'default' : 'error'}
              label={i18n._(t`Name`)}
            />
            <FormField
              name="approvalDescription"
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
                  {...timeoutMinutesField}
                  aria-label={i18n._(t`Timeout minutes`)}
                  id="approval-timeout-minutes"
                  min="0"
                  onChange={(value, event) => {
                    timeoutMinutesField.onChange(event);
                  }}
                  step="1"
                  type="number"
                />
                <TimeoutLabel>
                  <Trans>min</Trans>
                </TimeoutLabel>
                <TimeoutInput
                  {...timeoutSecondsField}
                  aria-label={i18n._(t`Timeout seconds`)}
                  id="approval-timeout-seconds"
                  min="0"
                  onChange={(value, event) => {
                    timeoutSecondsField.onChange(event);
                  }}
                  step="1"
                  type="number"
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
