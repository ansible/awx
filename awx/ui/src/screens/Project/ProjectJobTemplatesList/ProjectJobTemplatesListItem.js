import 'styled-components/macro';
import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import {
  ExclamationTriangleIcon,
  PencilAltIcon,
  RocketIcon,
} from '@patternfly/react-icons';
import { t } from '@lingui/macro';
import styled from 'styled-components';

import { ActionsTd, ActionItem } from 'components/PaginatedTable';
import { LaunchButton } from 'components/LaunchButton';
import Sparkline from 'components/Sparkline';
import { toTitleCase } from 'util/strings';

const ExclamationTriangleIconWarning = styled(ExclamationTriangleIcon)`
  color: var(--pf-global--warning-color--100);
  margin-left: 18px;
`;

function ProjectJobTemplateListItem({
  template,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
}) {
  const canLaunch = template.summary_fields.user_capabilities.start;

  const missingResourceIcon =
    template.type === 'job_template' &&
    (!template.summary_fields.project ||
      (!template.summary_fields.inventory &&
        !template.ask_inventory_on_launch));

  const missingExecutionEnvironment =
    template.type === 'job_template' &&
    template.custom_virtualenv &&
    !template.execution_environment;

  return (
    <Tr id={`template-row-${template.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
      />
      <Td dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          {template.name}
          {missingResourceIcon && (
            <Tooltip
              content={t`Resources are missing from this template.`}
              position="right"
            >
              <ExclamationTriangleIcon css="color: #c9190b; margin-left: 20px;" />
            </Tooltip>
          )}
          {missingExecutionEnvironment && (
            <Tooltip
              content={t`Custom virtual environment ${template.custom_virtualenv} must be replaced by an execution environment.`}
              position="right"
              className="missing-execution-environment"
            >
              <ExclamationTriangleIconWarning />
            </Tooltip>
          )}
        </Link>
      </Td>
      <Td dataLabel={t`Type`}>{toTitleCase(template.type)}</Td>
      <Td dataLabel={t`Recent jobs`}>
        <Sparkline jobs={template.summary_fields.recent_jobs} />
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          visible={canLaunch && template.type === 'job_template'}
          tooltip={t`Launch Template`}
        >
          <LaunchButton resource={template}>
            {({ handleLaunch, isLaunching }) => (
              <Button
                ouiaId={`${template.id}-launch-button`}
                css="grid-column: 1"
                variant="plain"
                onClick={handleLaunch}
                isDisabled={isLaunching}
              >
                <RocketIcon />
              </Button>
            )}
          </LaunchButton>
        </ActionItem>
        <ActionItem
          visible={template.summary_fields.user_capabilities.edit}
          tooltip={t`Edit Template`}
        >
          <Button
            ouiaId={`${template.id}-edit-button`}
            css="grid-column: 2"
            variant="plain"
            component={Link}
            to={`/templates/${template.type}/${template.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

export { ProjectJobTemplateListItem as _ProjectJobTemplateListItem };
export default ProjectJobTemplateListItem;
