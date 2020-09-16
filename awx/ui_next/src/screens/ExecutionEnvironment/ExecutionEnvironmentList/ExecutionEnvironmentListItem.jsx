import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button,
  DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';

import DataListCell from '../../../components/DataListCell';
import { ExecutionEnvironment } from '../../../types';

function ExecutionEnvironmentListItem({
  executionEnvironment,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
}) {
  const labelId = `check-action-${executionEnvironment.id}`;

  return (
    <DataListItem
      key={executionEnvironment.id}
      aria-labelledby={labelId}
      id={`${executionEnvironment.id} `}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-execution-environment-${executionEnvironment.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell
              key="image"
              aria-label={i18n._(t`execution environment image`)}
            >
              <Link to={`${detailUrl}`}>
                <b>{executionEnvironment.image}</b>
              </Link>
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          <Tooltip
            content={i18n._(t`Edit execution environment`)}
            position="top"
          >
            <Button
              aria-label={i18n._(t`Edit execution environment`)}
              variant="plain"
              component={Link}
              to={`/execution_environments/${executionEnvironment.id}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </Tooltip>
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

ExecutionEnvironmentListItem.prototype = {
  executionEnvironment: ExecutionEnvironment.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(ExecutionEnvironmentListItem);
