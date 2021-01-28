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
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import {
  DetailList,
  Detail,
  DeletedDetail,
} from '../../../components/DetailList';
import ChipGroup from '../../../components/ChipGroup';
import CredentialChip from '../../../components/CredentialChip';
import { timeOfDay } from '../../../util/dates';

import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../api';
import LaunchButton from '../../../components/LaunchButton';
import Sparkline from '../../../components/Sparkline';
import { toTitleCase } from '../../../util/strings';
import { formatDateString } from '../../../util/dates';
import CopyButton from '../../../components/CopyButton';

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
        </Td>
        <Td dataLabel={i18n._(t`Type`)}>{toTitleCase(template.type)}</Td>
        <Td dataLabel={i18n._(t`Last Ran`)}>{lastRun}</Td>
        <ActionsTd dataLabel={i18n._(t`Actions`)}>
          <ActionItem
            visible={template.type === 'workflow_job_template'}
            tooltip={i18n._(t`Visualizer`)}
          >
            <Button
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
          <ActionItem visible={template.summary_fields.user_capabilities.copy}>
            <CopyButton
              id={`template-action-copy-${template.id}`}
              helperText={{
                errorMessage: i18n._(t`Failed to copy template.`),
                tooltip: i18n._(t`Copy Template`),
              }}
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
                label={i18n._(t`Activity`)}
                value={<Sparkline jobs={summaryFields.recent_jobs} />}
                dataCy={`template-${template.id}-activity`}
              />
              {summaryFields.credentials && summaryFields.credentials.length && (
                <Detail
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
                !askInventoryOnLaunch && (
                  <DeletedDetail label={i18n._(t`Inventory`)} />
                )
              )}
              {summaryFields.labels && summaryFields.labels.results.length > 0 && (
                <Detail
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
              <Detail
                label={i18n._(t`Last Modified`)}
                value={formatDateString(template.modified)}
                dataCy={`template-${template.id}-last-modified`}
              />
            </DetailList>
          </ExpandableRowContent>
        </Td>
      </Tr>
    </>
  );
}

export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
