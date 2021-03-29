import 'styled-components/macro';
import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import styled from 'styled-components';
import { useField } from 'formik';
import {
  Alert,
  Form,
  FormGroup,
  TextInput,
  Select,
  SelectVariant,
  SelectOption,
} from '@patternfly/react-core';
import { required } from '../../../../../../util/validators';

import {
  FormColumnLayout,
  FormFullWidthLayout,
} from '../../../../../../components/FormLayout';
import Popover from '../../../../../../components/Popover';
import AnsibleSelect from '../../../../../../components/AnsibleSelect';
import InventorySourcesList from './InventorySourcesList';
import JobTemplatesList from './JobTemplatesList';
import ProjectsList from './ProjectsList';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';
import FormField from '../../../../../../components/FormField';

const NodeTypeErrorAlert = styled(Alert)`
  margin-bottom: 20px;
`;

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
  const [nodeResourceField, nodeResourceMeta, nodeResourceHelpers] = useField(
    'nodeResource'
  );
  const [, approvalNameMeta, approvalNameHelpers] = useField('approvalName');
  const [, , approvalDescriptionHelpers] = useField('approvalDescription');
  const [timeoutMinutesField, , timeoutMinutesHelpers] = useField(
    'timeoutMinutes'
  );
  const [timeoutSecondsField, , timeoutSecondsHelpers] = useField(
    'timeoutSeconds'
  );
  const [convergenceField, , convergenceFieldHelpers] = useField('convergence');

  const [isConvergenceOpen, setIsConvergenceOpen] = useState(false);

  const isValid = !approvalNameMeta.touched || !approvalNameMeta.error;
  return (
    <>
      {nodeResourceMeta.error && (
        <NodeTypeErrorAlert
          variant="danger"
          isInline
          title={nodeResourceMeta.error}
        />
      )}
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
              convergenceFieldHelpers.setValue('any');
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
      <Form css="margin-top: 20px;">
        <FormColumnLayout>
          {nodeTypeField.value === 'workflow_approval_template' && (
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
          )}
          <FormGroup
            fieldId="convergence"
            label={i18n._(t`Convergence`)}
            isRequired
            labelIcon={
              <Popover
                content={
                  <>
                    {i18n._(
                      t`Preconditions for running this node when there are multiple parents. Refer to the`
                    )}{' '}
                    <a
                      href="https://docs.ansible.com/ansible-tower/latest/html/userguide/workflow_templates.html#convergence-node"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {i18n._(t`documentation`)}
                    </a>{' '}
                    {i18n._(t`for more info.`)}
                  </>
                }
              />
            }
          >
            <Select
              variant={SelectVariant.single}
              isOpen={isConvergenceOpen}
              selections={convergenceField.value}
              onToggle={setIsConvergenceOpen}
              onSelect={(event, selection) => {
                convergenceFieldHelpers.setValue(selection);
                setIsConvergenceOpen(false);
              }}
              aria-label={i18n._(t`Convergence select`)}
              id="convergence-select"
            >
              <SelectOption key="any" value="any">
                {i18n._(t`Any`)}
              </SelectOption>
              <SelectOption key="all" value="all">
                {i18n._(t`All`)}
              </SelectOption>
            </Select>
          </FormGroup>
        </FormColumnLayout>
      </Form>
    </>
  );
}
export default withI18n()(NodeTypeStep);
