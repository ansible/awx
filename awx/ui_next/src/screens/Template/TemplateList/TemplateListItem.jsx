import 'styled-components/macro';
import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  ExclamationTriangleIcon,
  PencilAltIcon,
  ProjectDiagramIcon,
  RocketIcon,
} from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { timeOfDay } from '../../../util/dates';

import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../api';
import LaunchButton from '../../../components/LaunchButton';
import Sparkline from '../../../components/Sparkline';
import { toTitleCase } from '../../../util/strings';
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
    <Tr id={`template-row-${template.id}`}>
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
      <Td dataLabel={i18n._(t`Recent Jobs`)}>
        <Sparkline jobs={template.summary_fields.recent_jobs} />
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={template.type === 'workflow_job_template'}
          tooltip={i18n._(t`Visualizer`)}
        >
          <Button
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
          visible={template.summary_fields.user_capabilities.copy}
          tooltip={i18n._(t`Copy Template`)}
        >
          <CopyButton
            helperText={{
              errorMessage: i18n._(t`Failed to copy template.`),
            }}
            isDisabled={isDisabled}
            onCopyStart={handleCopyStart}
            onCopyFinish={handleCopyFinish}
            copyItem={copyTemplate}
          />
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
