import React from 'react';
import { withI18n } from '@lingui/react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Button,
  DataListItem,
  DataListItemRow,
  DataListCheck,
  DataListItemCells,
  DataListCell,
  DataListAction,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import StatusIcon from '../../../components/StatusIcon';
import InventorySourceSyncButton from '../shared/InventorySourceSyncButton';

function InventorySourceListItem({
  source,
  isSelected,
  onSelect,
  i18n,
  detailUrl,
  label,
}) {
  const generateLastJobTooltip = job => {
    return (
      <>
        <div>{i18n._(t`MOST RECENT SYNC`)}</div>
        <div>
          {i18n._(t`JOB ID:`)} {job.id}
        </div>
        <div>
          {i18n._(t`STATUS:`)} {job.status.toUpperCase()}
        </div>
        {job.finished && (
          <div>
            {i18n._(t`FINISHED:`)} {job.finished}
          </div>
        )}
      </>
    );
  };
  return (
    <>
      <DataListItem aria-labelledby={`check-action-${source.id}`}>
        <DataListItemRow>
          <DataListCheck
            id={`select-source-${source.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={`check-action-${source.id}`}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="status" isFilled={false}>
                {source.summary_fields.last_job && (
                  <Tooltip
                    position="top"
                    content={generateLastJobTooltip(
                      source.summary_fields.last_job
                    )}
                    key={source.summary_fields.last_job.id}
                  >
                    <Link
                      to={`/jobs/inventory/${source.summary_fields.last_job.id}`}
                    >
                      <StatusIcon
                        status={source.summary_fields.last_job.status}
                      />
                    </Link>
                  </Tooltip>
                )}
              </DataListCell>,
              <DataListCell aria-label={i18n._(t`name`)} key="name">
                <span>
                  <Link to={`${detailUrl}/details`}>
                    <b>{source.name}</b>
                  </Link>
                </span>
              </DataListCell>,
              <DataListCell aria-label={i18n._(t`type`)} key="type">
                {label}
              </DataListCell>,
            ]}
          />
          <DataListAction
            id="actions"
            aria-labelledby="actions"
            aria-label="actions"
          >
            {source.summary_fields.user_capabilities.start && (
              <InventorySourceSyncButton source={source} />
            )}
            {source.summary_fields.user_capabilities.edit && (
              <Button
                aria-label={i18n._(t`Edit Source`)}
                variant="plain"
                component={Link}
                to={`${detailUrl}/edit`}
              >
                <PencilAltIcon />
              </Button>
            )}
          </DataListAction>
        </DataListItemRow>
      </DataListItem>
    </>
  );
}
export default withI18n()(InventorySourceListItem);
