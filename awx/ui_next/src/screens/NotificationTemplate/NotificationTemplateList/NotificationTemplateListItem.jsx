import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Badge as PFBadge,
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Tooltip,
} from '@patternfly/react-core';
import DataListCell from '../../../components/DataListCell';

export default function NotificationTemplatesListItem({
  template,
  detailUrl,
  isSelected,
  onSelect,
}) {
  const labelId = `check-action-${template.id}`;
  return (
    <DataListItem key={template.id} aria-labelledby={labelId} id={template.id}>
      <DataListItemRow>
        <DataListCheck
          id={`select-template-${template.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" id={labelId}>
              <Link to={detailUrl}>
                <b>{template.name}</b>
              </Link>
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}
