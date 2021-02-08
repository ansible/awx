import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';

import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { ExecutionEnvironment } from '../../../types';

function ExecutionEnvironmentListItem({
  executionEnvironment,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
  rowIndex,
}) {
  const labelId = `check-action-${executionEnvironment.id}`;

  return (
    <Tr id={`ee-row-${executionEnvironment.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
          disable: false,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${detailUrl}`}>
          <b>{executionEnvironment.name}</b>
        </Link>
      </Td>
      <Td id={labelId} dataLabel={i18n._(t`Image`)}>
        {executionEnvironment.image}
      </Td>
      <Td id={labelId} dataLabel={i18n._(t`Organization`)}>
        {executionEnvironment.organization ? (
          <Link
            to={`/organizations/${executionEnvironment?.summary_fields?.organization?.id}/details`}
          >
            <b>{executionEnvironment?.summary_fields?.organization?.name}</b>
          </Link>
        ) : (
          i18n._(t`Globally Available`)
        )}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={executionEnvironment.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit Execution Environment`)}
        >
          <Button
            aria-label={i18n._(t`Edit Execution Environment`)}
            variant="plain"
            component={Link}
            to={`/execution_environments/${executionEnvironment.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

ExecutionEnvironmentListItem.prototype = {
  executionEnvironment: ExecutionEnvironment.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(ExecutionEnvironmentListItem);
