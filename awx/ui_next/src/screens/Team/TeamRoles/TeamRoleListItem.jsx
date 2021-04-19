import React from 'react';

import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Chip,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import { DetailList, Detail } from '../../../components/DetailList';
import DataListCell from '../../../components/DataListCell';

function TeamRoleListItem({ role, detailUrl, onSelect }) {
  const labelId = `teamRole-${role.id}`;
  return (
    <DataListItem key={role.id} aria-labelledby={labelId} id={`${role.id}`}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={t`resource name`}>
              <Link to={`${detailUrl}`} id={labelId}>
                <b>{role.summary_fields.resource_name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type" aria-label={t`resource type`}>
              {role.summary_fields && (
                <DetailList stacked>
                  <Detail
                    label={t`Type`}
                    value={role.summary_fields.resource_type_display_name}
                  />
                </DetailList>
              )}
            </DataListCell>,
            <DataListCell key="role" aria-label={t`resource role`}>
              {role.name && (
                <DetailList stacked>
                  <Detail
                    label={t`Role`}
                    value={
                      <Chip
                        key={role.name}
                        aria-label={role.name}
                        onClick={() => onSelect(role)}
                        isReadOnly={
                          !role.summary_fields.user_capabilities.unattach
                        }
                      >
                        {role.name}
                      </Chip>
                    }
                  />
                </DetailList>
              )}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}
export default TeamRoleListItem;
