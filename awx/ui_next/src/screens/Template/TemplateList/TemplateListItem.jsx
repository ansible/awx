import React from 'react';
import { Link } from 'react-router-dom';
import {
  Button,
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
  RocketIcon,
} from '@patternfly/react-icons';

import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import LaunchButton from '@components/LaunchButton';
import VerticalSeparator from '@components/VerticalSeparator';
import { Sparkline } from '@components/Sparkline';
import { toTitleCase } from '@util/strings';

function TemplateListItem({ i18n, template, isSelected, onSelect, detailUrl }) {
  const canLaunch = template.summary_fields.user_capabilities.start;

  const missingResourceIcon =
    template.type === 'job_template' &&
    (!template.summary_fields.project ||
      (!template.summary_fields.inventory &&
        !template.ask_inventory_on_launch));

  return (
    <DataListItem
      aria-labelledby={`check-action-${template.id}`}
      id={`${template.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-jobTemplate-${template.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={`check-action-${template.id}`}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="divider">
              <VerticalSeparator />
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
            <DataListCell alignRight isFilled={false} key="launch">
              {canLaunch && template.type === 'job_template' && (
                <Tooltip content={i18n._(t`Launch Template`)} position="top">
                  <LaunchButton resource={template}>
                    {({ handleLaunch }) => (
                      <Button variant="plain" onClick={handleLaunch}>
                        <RocketIcon />
                      </Button>
                    )}
                  </LaunchButton>
                </Tooltip>
              )}
            </DataListCell>,
            <DataListCell key="edit" alignRight isFilled={false}>
              {template.summary_fields.user_capabilities.edit && (
                <Tooltip content={i18n._(t`Edit Template`)} position="top">
                  <Button
                    variant="plain"
                    component={Link}
                    to={`/templates/${template.type}/${template.id}/edit`}
                  >
                    <PencilAltIcon />
                  </Button>
                </Tooltip>
              )}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
