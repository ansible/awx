import 'styled-components/macro';
import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { Host } from '../../../types';
import HostToggle from '../../../components/HostToggle';

function HostListItem({
  i18n,
  host,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
}) {
  const labelId = `check-action-${host.id}`;

  return (
    <Tr id={`host-row-${host.id}`}>
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
          <b>{host.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Inventory`)}>
        {host.summary_fields.inventory && (
          <Link
            to={`/inventories/inventory/${host.summary_fields.inventory.id}/details`}
          >
            {host.summary_fields.inventory.name}
          </Link>
        )}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)} gridColumns="auto 40px">
        <HostToggle host={host} />
        <ActionItem
          visible={host.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit Host`)}
        >
          <Button
            aria-label={i18n._(t`Edit Host`)}
            variant="plain"
            component={Link}
            to={`/hosts/${host.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

HostListItem.propTypes = {
  host: Host.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(HostListItem);
