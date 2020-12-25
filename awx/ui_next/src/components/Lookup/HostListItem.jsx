import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  TextContent,
} from '@patternfly/react-core';
import DataListCell from '../DataListCell';

function HostListItem({ item, i18n }) {
  return (
    <DataListItem
      aria-labelledby={`items-list-item-${item.id}`}
      key={item.id}
      id={`${item.id}`}
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={i18n._(t`name`)}>
              <TextContent>
                <Link to={{ pathname: item.url }}>
                  <b id={`items-list-item-${item.id}`}>{item.name}</b>
                </Link>
              </TextContent>
            </DataListCell>,
            <DataListCell key="inventory" aria-label={i18n._(t`inventory`)}>
              {item.summary_fields.inventory.name}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(HostListItem);
