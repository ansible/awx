import 'styled-components/macro';
import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  ExclamationTriangleIcon,
  PencilAltIcon,
  ProjectDiagramIcon,
  RocketIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import DataListCell from '../../../components/DataListCell';

import { timeOfDay } from '../../../util/dates';

import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../api';
import LaunchButton from '../../../components/LaunchButton';
import Sparkline from '../../../components/Sparkline';
import { toTitleCase } from '../../../util/strings';
import CopyButton from '../../../components/CopyButton';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(4, 40px);
`;

function TemplateListItem({
  i18n,
  template,
  isSelected,
  onSelect,
  detailUrl,
  fetchTemplates,
}) {
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

  const missingResourceIcon =
    template.type === 'job_template' &&
    (!template.summary_fields.project ||
      (!template.summary_fields.inventory &&
        !template.ask_inventory_on_launch));
  return (
    <DataListItem aria-labelledby={labelId} id={`${template.id}`}>
      <DataListItemRow>
        <DataListCheck
          isDisabled={isDisabled}
          id={`select-jobTemplate-${template.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" id={labelId}>
              <span>
                <Link to={`${detailUrl}`}>
                  <b>{template.name}</b>
                </Link>
              </span>
              {missingResourceIcon && (
                <span>
                  <Tooltip
                    content={i18n._(
                      t`Resources are missing from this template.`
                    )}
                    position="right"
                  >
                    <ExclamationTriangleIcon css="color: #c9190b; margin-left: 20px;" />
                  </Tooltip>
                </span>
              )}
            </DataListCell>,
            <DataListCell key="type">
              {toTitleCase(template.type)}
            </DataListCell>,
            <DataListCell key="sparkline">
              <Sparkline jobs={template.summary_fields.recent_jobs} />
            </DataListCell>,
          ]}
        />
        <DataListAction aria-label="actions" aria-labelledby={labelId}>
          {template.type === 'workflow_job_template' && (
            <Tooltip content={i18n._(t`Visualizer`)} position="top">
              <Button
                isDisabled={isDisabled}
                aria-label={i18n._(t`Visualizer`)}
                css="grid-column: 1"
                variant="plain"
                component={Link}
                to={`/templates/workflow_job_template/${template.id}/visualizer`}
              >
                <ProjectDiagramIcon />
              </Button>
            </Tooltip>
          )}
          {template.summary_fields.user_capabilities.start && (
            <Tooltip content={i18n._(t`Launch Template`)} position="top">
              <LaunchButton resource={template}>
                {({ handleLaunch }) => (
                  <Button
                    isDisabled={isDisabled}
                    aria-label={i18n._(t`Launch template`)}
                    css="grid-column: 2"
                    variant="plain"
                    onClick={handleLaunch}
                  >
                    <RocketIcon />
                  </Button>
                )}
              </LaunchButton>
            </Tooltip>
          )}
          {template.summary_fields.user_capabilities.edit && (
            <Tooltip content={i18n._(t`Edit Template`)} position="top">
              <Button
                isDisabled={isDisabled}
                aria-label={i18n._(t`Edit Template`)}
                css="grid-column: 3"
                variant="plain"
                component={Link}
                to={`/templates/${template.type}/${template.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
          {template.summary_fields.user_capabilities.copy && (
            <CopyButton
              helperText={{
                tooltip: i18n._(t`Copy Template`),
                errorMessage: i18n._(t`Failed to copy template.`),
              }}
              isDisabled={isDisabled}
              onCopyStart={handleCopyStart}
              onCopyFinish={handleCopyFinish}
              copyItem={copyTemplate}
            />
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
