import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { formatDateString } from '../../../util/dates';
import { Application } from '../../../types';

function ApplicationListItem({
  application,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
  i18n,
}) {
  const labelId = `check-action-${application.id}`;
  return (
    <Tr id={`application-row-${application.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${detailUrl}`}>
          <b>{application.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Organization`)}>
        <Link
          to={`/organizations/${application.summary_fields.organization.id}`}
        >
          <b>{application.summary_fields.organization.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Last Modified`)}>
        {formatDateString(application.modified)}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={application.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit application`)}
        >
          <Button
            aria-label={i18n._(t`Edit application`)}
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

export default withI18n()(ApplicationListItem);
