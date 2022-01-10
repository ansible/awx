import React from 'react';
import { string, bool, func } from 'prop-types';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem, TdBreakWord } from 'components/PaginatedTable';
import { formatDateString } from 'util/dates';
import { Application } from 'types';

function ApplicationListItem({
  application,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
}) {
  const labelId = `check-action-${application.id}`;
  return (
    <Tr
      id={`application-row-${application.id}`}
      ouiaId={`application-row-${application.id}`}
    >
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <TdBreakWord id={labelId} dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{application.name}</b>
        </Link>
      </TdBreakWord>
      <TdBreakWord dataLabel={t`Organization`}>
        <Link
          to={`/organizations/${application.summary_fields.organization.id}`}
        >
          <b>{application.summary_fields.organization.name}</b>
        </Link>
      </TdBreakWord>
      <Td dataLabel={t`Last Modified`}>
        {formatDateString(application.modified)}
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          visible={application.summary_fields.user_capabilities.edit}
          tooltip={t`Edit application`}
        >
          <Button
            ouiaId={`${application.id}-edit-button`}
            aria-label={t`Edit application`}
            variant="plain"
            component={Link}
            to={`/applications/${application.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

ApplicationListItem.propTypes = {
  application: Application.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default ApplicationListItem;
