import React from 'react';
import { string } from 'prop-types';

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';

import DataListCell from '../../../components/DataListCell';
import { ExecutionEnvironment } from '../../../types';

function OrganizationExecEnvListItem({ executionEnvironment, detailUrl }) {
  const labelId = `check-action-${executionEnvironment.id}`;

  return (
    <DataListItem
      key={executionEnvironment.id}
      aria-labelledby={labelId}
      id={`${executionEnvironment.id}`}
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={t`Execution environment name`}>
              <Link to={`${detailUrl}`}>
                <b>{executionEnvironment.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell
              key="image"
              aria-label={t`Execution environment image`}
            >
              {executionEnvironment.image}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

OrganizationExecEnvListItem.prototype = {
  executionEnvironment: ExecutionEnvironment.isRequired,
  detailUrl: string.isRequired,
};

export default OrganizationExecEnvListItem;
