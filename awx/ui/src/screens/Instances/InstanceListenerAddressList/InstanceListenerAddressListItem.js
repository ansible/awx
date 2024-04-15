import React from 'react';
import { t } from '@lingui/macro';
import 'styled-components/macro';
import { Tr, Td } from '@patternfly/react-table';

function InstanceListenerAddressListItem({
  peerListenerAddress,
  isSelected,
  onSelect,
  rowIndex,
}) {
  const labelId = `check-action-${peerListenerAddress.id}`;
  return (
    <Tr
      id={`peerListenerAddress-row-${peerListenerAddress.id}`}
      ouiaId={`peerListenerAddress-row-${peerListenerAddress.id}`}
    >
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />

      <Td id={labelId} dataLabel={t`Address`}>
        {peerListenerAddress.address}
      </Td>

      <Td id={labelId} dataLabel={t`Port`}>
        {peerListenerAddress.port}
      </Td>

      <Td id={labelId} dataLabel={t`Protocol`}>
        {peerListenerAddress.protocol}
      </Td>

      <Td id={labelId} dataLabel={t`Canonical`}>
        {peerListenerAddress.canonical.toString()}
      </Td>
    </Tr>
  );
}

export default InstanceListenerAddressListItem;
