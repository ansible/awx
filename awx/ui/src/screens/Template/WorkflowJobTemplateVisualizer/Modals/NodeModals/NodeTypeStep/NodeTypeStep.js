import 'styled-components/macro';
import React, { useState } from 'react';
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
import { required } from 'util/validators';

import { FormColumnLayout, FormFullWidthLayout } from 'components/FormLayout';
import Popover from 'components/Popover';
import AnsibleSelect from 'components/AnsibleSelect';
import FormField from 'components/FormField';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { useConfig, useUserProfile } from 'contexts/Config';
import InventorySourcesList from './InventorySourcesList';
import JobTemplatesList from './JobTemplatesList';
import ProjectsList from './ProjectsList';
import SystemJobTemplatesList from './SystemJobTemplatesList';
import WorkflowJobTemplatesList from './WorkflowJobTemplatesList';

const NodeTypeErrorAlert = styled(Alert)`
  margin-bottom: 20px;
`;

const TimeoutInput = styled(TextInput)`
  width: 200px !important;
  :not(:first-of-type) {
    margin-left: 20px;
  }
`;
TimeoutInput.displayName = 'TimeoutInput';

const TimeoutLabel = styled.p`
  margin-left: 10px;
  min-width: fit-content;
`;

function NodeTypeStep({ isIdentifierRequired }) {
  const { isSuperUser } = useUserProfile();
  const [nodeTypeField, , nodeTypeHelpers] = useField('nodeType');
  const [nodeResourceField, nodeResourceMeta, nodeResourceHelpers] =
    useField('nodeResource');
  const [, approvalNameMeta, approvalNameHelpers] = useField('approvalName');
  const [, , approvalDescriptionHelpers] = useField('approvalDescription');
  const [timeoutMinutesField, , timeoutMinutesHelpers] =
    useField('timeoutMinutes');
  const [timeoutSecondsField, , timeoutSecondsHelpers] =
    useField('timeoutSeconds');
  const [convergenceField, , convergenceFieldHelpers] = useField('convergence');

  const [isConvergenceOpen, setIsConvergenceOpen] = useState(false);
  const config = useConfig();

  const isValid = !approvalNameMeta.touched || !approvalNameMeta.error;
  const nodeTypeChoices = [
    {
      key: 'workflow_approval_template',
      value: 'workflow_approval_template',
      label: t`Approval`,
      isDisabled: false,
    },
    {
      key: 'inventory_source',
      value: 'inventory_source',
      label: t`Inventory Source Sync`,
      isDisabled: false,
    },
    {
      key: 'job_template',
      value: 'job_template',
      label: t`Job Template`,
      isDisabled: false,
    },
    {
      key: 'project',
      value: 'project',
      label: t`Project Sync`,
      isDisabled: false,
    },
    {
      key: 'workflow_job_template',
      value: 'workflow_job_template',
      label: t`Workflow Job Template`,
      isDisabled: false,
    },
  ];

  const modifiedNodeTypeChoices = isSuperUser
    ? [
        ...nodeTypeChoices,
        {
          key: 'system_job_template',
          value: 'system_job_template',
          label: t`Management Job`,
          isDisabled: false,
        },
      ]
    : nodeTypeChoices;

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
        <b css="margin-right: 24px">{t`Node Type`}</b>
        <div>
          <AnsibleSelect
            id="nodeResource-select"
            label={t`Select a Node Type`}
            data={modifiedNodeTypeChoices}
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
      {nodeTypeField.value === 'system_job_template' && (
        <SystemJobTemplatesList
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
      <Form autoComplete="off" css="margin-top: 20px;">
        <FormColumnLayout>
          <FormFullWidthLayout>
            {nodeTypeField.value === 'workflow_approval_template' && (
              <>
                <FormField
                  name="approvalName"
                  id="approval-name"
                  isRequired
                  validate={required(null)}
                  validated={isValid ? 'default' : 'error'}
                  label={t`Name`}
                />
                <FormField
                  name="approvalDescription"
                  id="approval-description"
                  label={t`Description`}
                />
                <FormGroup
                  label={t`Timeout`}
                  fieldId="approval-timeout"
                  name="timeout"
                >
                  <div css="display: flex;align-items: center;">
                    <TimeoutInput
                      {...timeoutMinutesField}
                      aria-label={t`Timeout minutes`}
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
                      aria-label={t`Timeout seconds`}
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
              </>
            )}
            <FormGroup
              fieldId="convergence"
              label={t`Convergence`}
              isRequired
              labelIcon={
                <Popover
                  content={
                    <>
                      {t`Preconditions for running this node when there are multiple parents. Refer to the`}{' '}
                      <a
                        href={`${getDocsBaseUrl(
                          config
                        )}/html/userguide/workflow_templates.html#convergence-node`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {t`documentation`}
                      </a>{' '}
                      {t`for more info.`}
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
                aria-label={t`Convergence select`}
                typeAheadAriaLabel={t`Convergence select`}
                className="convergenceSelect"
                ouiaId="convergenceSelect"
                noResultsFoundText={t`No results found`}
              >
                <SelectOption key="any" value="any" id="select-option-any">
                  {t`Any`}
                </SelectOption>
                <SelectOption key="all" value="all" id="select-option-all">
                  {t`All`}
                </SelectOption>
              </Select>
            </FormGroup>
            <FormField
              id="node-alias"
              name="identifier"
              aria-label={t`Node Alias`}
              label={t`Node Alias`}
              tooltip={t`If specified, this field will be shown on the node instead of the resource name when viewing the workflow`}
              isRequired={isIdentifierRequired}
              validate={isIdentifierRequired ? required(null) : null}
              validated={isValid ? 'default' : 'error'}
            />
          </FormFullWidthLayout>
        </FormColumnLayout>
      </Form>
    </>
  );
}
export default NodeTypeStep;
