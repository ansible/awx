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
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';

function InventorySourceListItem({
  source,
  isSelected,
  onSelect,
  i18n,
  detailUrl,
  label,
}) {
  return (
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
  );
}
export default withI18n()(InventorySourceListItem);
