import React from 'react';
import { t } from '@lingui/macro';
import { Td, Tr } from '@patternfly/react-table';

function HostListItem({ item }) {
  return (
    <Tr ouiaId={`host-list-item-${item.id}`}>
      <Td dataLabel={t`Name`}>{item.name}</Td>
      <Td dataLabel={t`Description`}>{item.description}</Td>
      <Td dataLabel={t`Inventory`}>{item.summary_fields.inventory.name}</Td>
    </Tr>
  );
}

export default HostListItem;
