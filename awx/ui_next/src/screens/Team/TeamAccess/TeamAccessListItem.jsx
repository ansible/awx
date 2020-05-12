import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemCells,
  DataListItemRow,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import DataListCell from '../../../components/DataListCell';

function TeamAccessListItem({ role, i18n, detailUrl }) {
  const labelId = `teamRole-${role.id}`;
  return (
    <DataListItem key={role.id} aria-labelledby={labelId} id={`${role.id}`}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={i18n._(t`resource name`)}>
              <Link to={`${detailUrl}`} id={labelId}>
                <b>{role.summary_fields.resource_name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type" aria-label={i18n._(t`resource type`)}>
              {role.summary_fields && (
                <>
                  <b css="margin-right: 24px">{i18n._(t`Type`)}</b>
                  {role.summary_fields.resource_type_display_name}
                </>
              )}
            </DataListCell>,
            <DataListCell key="role" aria-label={i18n._(t`resource role`)}>
              {role.name && (
                <>
                  <b css="margin-right: 24px">{i18n._(t`Role`)}</b>
                  {role.name}
                </>
              )}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}
export default withI18n()(TeamAccessListItem);
