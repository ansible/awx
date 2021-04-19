import React, { useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';

import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import CopyButton from '../../../components/CopyButton';
import { ExecutionEnvironment } from '../../../types';
import { ExecutionEnvironmentsAPI } from '../../../api';
import { timeOfDay } from '../../../util/dates';

function ExecutionEnvironmentListItem({
  executionEnvironment,
  detailUrl,
  isSelected,
  onSelect,

  rowIndex,
  fetchExecutionEnvironments,
}) {
  const [isDisabled, setIsDisabled] = useState(false);

  const copyExecutionEnvironment = useCallback(async () => {
    await ExecutionEnvironmentsAPI.copy(executionEnvironment.id, {
      name: `${executionEnvironment.name} @ ${timeOfDay()}`,
    });
    await fetchExecutionEnvironments();
  }, [
    executionEnvironment.id,
    executionEnvironment.name,
    fetchExecutionEnvironments,
  ]);

  const handleCopyStart = useCallback(() => {
    setIsDisabled(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsDisabled(false);
  }, []);

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
        dataLabel={t`Selected`}
      />
      <Td id={labelId} dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{executionEnvironment.name}</b>
        </Link>
      </Td>
      <Td id={labelId} dataLabel={t`Image`}>
        {executionEnvironment.image}
      </Td>
      <Td id={labelId} dataLabel={t`Organization`}>
        {executionEnvironment.organization ? (
          <Link
            to={`/organizations/${executionEnvironment?.summary_fields?.organization?.id}/details`}
          >
            <b>{executionEnvironment?.summary_fields?.organization?.name}</b>
          </Link>
        ) : (
          t`Globally Available`
        )}
      </Td>
      <ActionsTd dataLabel={t`Actions`} gridColumns="auto 40px">
        <ActionItem
          visible={executionEnvironment.summary_fields.user_capabilities.edit}
          tooltip={t`Edit Execution Environment`}
        >
          <Button
            ouiaId={`${executionEnvironment.id}-edit-button`}
            aria-label={t`Edit Execution Environment`}
            variant="plain"
            component={Link}
            to={`/execution_environments/${executionEnvironment.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
        <ActionItem
          visible={executionEnvironment.summary_fields.user_capabilities.copy}
          tooltip={t`Copy Execution Environment`}
        >
          <CopyButton
            ouiaId={`copy-ee-${executionEnvironment.id}`}
            isDisabled={isDisabled}
            onCopyStart={handleCopyStart}
            onCopyFinish={handleCopyFinish}
            copyItem={copyExecutionEnvironment}
            errorMessage={t`Failed to copy execution environment`}
          />
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

export default ExecutionEnvironmentListItem;
