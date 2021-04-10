import 'styled-components/macro';
import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Button, Tooltip, Chip } from '@patternfly/react-core';
import { Tr, Td, ExpandableRowContent } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  ExclamationTriangleIcon,
  PencilAltIcon,
  ProjectDiagramIcon,
  RocketIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';

import { ActionsTd, ActionItem } from '../PaginatedTable';
import { DetailList, Detail, DeletedDetail } from '../DetailList';
import ChipGroup from '../ChipGroup';
import CredentialChip from '../CredentialChip';
import ExecutionEnvironmentDetail from '../ExecutionEnvironmentDetail';
import { timeOfDay, formatDateString } from '../../util/dates';

import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../api';
import { LaunchButton } from '../LaunchButton';
import Sparkline from '../Sparkline';
import { toTitleCase } from '../../util/strings';
import CopyButton from '../CopyButton';

const ExclamationTriangleIconWarning = styled(ExclamationTriangleIcon)`
  color: var(--pf-global--warning-color--100);
  margin-left: 18px;
`;

function TemplateListItem({
  i18n,
  template,
  isSelected,
  onSelect,
  detailUrl,
  fetchTemplates,
  rowIndex,
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDisabled, setIsDisabled] = useState(false);
  const labelId = `check-action-${template.id}`;

  const copyTemplate = useCallback(async () => {
    if (template.type === 'job_template') {
      await JobTemplatesAPI.copy(template.id, {
        name: `${template.name} @ ${timeOfDay()}`,
      });
    } else {
      await WorkflowJobTemplatesAPI.copy(template.id, {
        name: `${template.name} @ ${timeOfDay()}`,
      });
    }
    await fetchTemplates();
  }, [fetchTemplates, template.id, template.name, template.type]);

  const handleCopyStart = useCallback(() => {
    setIsDisabled(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsDisabled(false);
  }, []);

  const {
    summary_fields: summaryFields,
    ask_inventory_on_launch: askInventoryOnLaunch,
  } = template;

  const missingResourceIcon =
    template.type === 'job_template' &&
    (!summaryFields.project ||
      (!summaryFields.inventory && !askInventoryOnLaunch));

  const missingExecutionEnvironment =
    template.type === 'job_template' &&
    template.custom_virtualenv &&
    !template.execution_environment;

  const inventoryValue = (kind, id) => {
    const inventorykind = kind === 'smart' ? 'smart_inventory' : 'inventory';

    return askInventoryOnLaunch ? (
      <>
        <Link to={`/inventories/${inventorykind}/${id}/details`}>
          {summaryFields.inventory.name}
        </Link>
        <span> {i18n._(t`(Prompt on launch)`)}</span>
      </>
    ) : (
      <Link to={`/inventories/${inventorykind}/${id}/details`}>
        {summaryFields.inventory.name}
      </Link>
    );
  };
  let lastRun = '';
  const mostRecentJob = template.summary_fields.recent_jobs
    ? template.summary_fields.recent_jobs[0]
    : null;
  if (mostRecentJob) {
    lastRun = mostRecentJob.finished
      ? formatDateString(mostRecentJob.finished)
      : i18n._(t`Running`);
  }

  return (
    <>
      <Tr id={`template-row-${template.id}`}>
        <Td
          expand={{
            rowIndex,
            isExpanded,
            onToggle: () => setIsExpanded(!isExpanded),
          }}
        />
        <Td
          select={{
            rowIndex,
            isSelected,
            onSelect,
          }}
          dataLabel={i18n._(t`Selected`)}
        />
        <Td id={labelId} dataLabel={i18n._(t`Name`)}>
          <Link to={`${detailUrl}`}>
            <b>{template.name}</b>
          </Link>
          {missingResourceIcon && (
            <span>
              <Tooltip
                content={i18n._(t`Resources are missing from this template.`)}
                position="right"
              >
                <ExclamationTriangleIcon css="color: #c9190b; margin-left: 20px;" />
              </Tooltip>
            </span>
          )}
          {missingExecutionEnvironment && (
            <span>
              <Tooltip
                className="missing-execution-environment"
                content={i18n._(
                  t`Custom virtual environment ${template.custom_virtualenv} must be replaced by an execution environment.`
                )}
                position="right"
              >
                <ExclamationTriangleIconWarning />
              </Tooltip>
            </span>
          )}
        </Td>
        <Td dataLabel={i18n._(t`Type`)}>{toTitleCase(template.type)}</Td>
        <Td dataLabel={i18n._(t`Last Ran`)}>{lastRun}</Td>
        <ActionsTd dataLabel={i18n._(t`Actions`)}>
          <ActionItem
            visible={template.type === 'workflow_job_template'}
            tooltip={i18n._(t`Visualizer`)}
          >
            <Button
              ouiaId={`${template.id}-visualizer-button`}
              id={`template-action-visualizer-${template.id}`}
              isDisabled={isDisabled}
              aria-label={i18n._(t`Visualizer`)}
              variant="plain"
              component={Link}
              to={`/templates/workflow_job_template/${template.id}/visualizer`}
            >
              <ProjectDiagramIcon />
            </Button>
          </ActionItem>
          <ActionItem
            visible={template.summary_fields.user_capabilities.start}
            tooltip={i18n._(t`Launch Template`)}
          >
            <LaunchButton resource={template}>
              {({ handleLaunch }) => (
                <Button
                  ouiaId={`${template.id}-launch-button`}
                  id={`template-action-launch-${template.id}`}
                  isDisabled={isDisabled}
                  aria-label={i18n._(t`Launch template`)}
                  variant="plain"
                  onClick={handleLaunch}
                >
                  <RocketIcon />
                </Button>
              )}
            </LaunchButton>
          </ActionItem>
          <ActionItem
            visible={template.summary_fields.user_capabilities.edit}
            tooltip={i18n._(t`Edit Template`)}
          >
            <Button
              ouiaId={`${template.id}-edit-button`}
              id={`template-action-edit-${template.id}`}
              isDisabled={isDisabled}
              aria-label={i18n._(t`Edit Template`)}
              variant="plain"
              component={Link}
              to={`/templates/${template.type}/${template.id}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </ActionItem>
          <ActionItem
            tooltip={i18n._(t`Copy Template`)}
            visible={template.summary_fields.user_capabilities.copy}
          >
            <CopyButton
              id={`template-action-copy-${template.id}`}
              errorMessage={i18n._(t`Failed to copy template.`)}
              isDisabled={isDisabled}
              onCopyStart={handleCopyStart}
              onCopyFinish={handleCopyFinish}
              copyItem={copyTemplate}
            />
          </ActionItem>
        </ActionsTd>
      </Tr>
      <Tr isExpanded={isExpanded}>
        <Td colSpan={2} />
        <Td colSpan={4}>
          <ExpandableRowContent>
            <DetailList>
              <Detail
                label={i18n._(t`Description`)}
                value={template.description}
                dataCy={`template-${template.id}-description`}
              />
              {summaryFields.recent_jobs && summaryFields.recent_jobs.length ? (
                <Detail
                  label={i18n._(t`Activity`)}
                  value={<Sparkline jobs={summaryFields.recent_jobs} />}
                  dataCy={`template-${template.id}-activity`}
                />
              ) : null}
              {summaryFields.organization && (
                <Detail
                  label={i18n._(t`Organization`)}
                  value={
                    <Link
                      to={`/organizations/${summaryFields.organization.id}/details`}
                    >
                      {summaryFields.organization.name}
                    </Link>
                  }
                  dataCy={`template-${template.id}-organization`}
                />
              )}
              {summaryFields.inventory ? (
                <Detail
                  label={i18n._(t`Inventory`)}
                  value={inventoryValue(
                    summaryFields.inventory.kind,
                    summaryFields.inventory.id
                  )}
                  dataCy={`template-${template.id}-inventory`}
                />
              ) : (
                !askInventoryOnLaunch &&
                template.type === 'job_template' && (
                  <DeletedDetail label={i18n._(t`Inventory`)} />
                )
              )}
              {summaryFields.project && (
                <Detail
                  label={i18n._(t`Project`)}
                  value={
                    <Link to={`/projects/${summaryFields.project.id}/details`}>
                      {summaryFields.project.name}
                    </Link>
                  }
                  dataCy={`template-${template.id}-project`}
                />
              )}
              <ExecutionEnvironmentDetail
                virtualEnvironment={template.custom_virtualenv}
                executionEnvironment={summaryFields?.execution_environment}
              />
              <Detail
                label={i18n._(t`Last Modified`)}
                value={formatDateString(template.modified)}
                dataCy={`template-${template.id}-last-modified`}
              />
              {summaryFields.credentials && summaryFields.credentials.length ? (
                <Detail
                  fullWidth
                  label={i18n._(t`Credentials`)}
                  value={
                    <ChipGroup
                      numChips={5}
                      totalChips={summaryFields.credentials.length}
                    >
                      {summaryFields.credentials.map(c => (
                        <CredentialChip key={c.id} credential={c} isReadOnly />
                      ))}
                    </ChipGroup>
                  }
                  dataCy={`template-${template.id}-credentials`}
                />
              ) : null}
              {summaryFields.labels && summaryFields.labels.results.length > 0 && (
                <Detail
                  fullWidth
                  label={i18n._(t`Labels`)}
                  value={
                    <ChipGroup
                      numChips={5}
                      totalChips={summaryFields.labels.results.length}
                    >
                      {summaryFields.labels.results.map(l => (
                        <Chip key={l.id} isReadOnly>
                          {l.name}
                        </Chip>
                      ))}
                    </ChipGroup>
                  }
                  dataCy={`template-${template.id}-labels`}
                />
              )}
            </DetailList>
          </ExpandableRowContent>
        </Td>
      </Tr>
    </>
  );
}

export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
