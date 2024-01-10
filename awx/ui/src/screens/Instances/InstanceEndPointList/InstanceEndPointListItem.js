import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import 'styled-components/macro';
import { Tr, Td } from '@patternfly/react-table';

function InstanceEndPointListItem({
  peerEndpoint,
  isSelected,
  onSelect,
  isExpanded,
  onExpand,
  rowIndex,
}) {
  const labelId = `check-action-${peerEndpoint.id}`;
  return (
    <Tr
      id={`peerEndpoint-row-${peerEndpoint.id}`}
      ouiaId={`peerEndpoint-row-${peerEndpoint.id}`}
    >
      <Td
        expand={{
          rowIndex,
          isExpanded,
          onToggle: onExpand,
        }}
      />

      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />

      <Td id={labelId} dataLabel={t`Address`}>
          {peerEndpoint.address}
      </Td>

      <Td id={labelId} dataLabel={t`Port`}>
          {peerEndpoint.port}
      </Td>

      <Td id={labelId} dataLabel={t`Canonical`}>
          {peerEndpoint.canonical.toString()}
      </Td>

    </Tr>
  );
}

export default InstanceEndPointListItem;
