import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import 'styled-components/macro';
import { Tr, Td } from '@patternfly/react-table';

function InstanceEndPointListItem({
  peerInstance,
  isSelected,
  onSelect,
  isExpanded,
  onExpand,
  rowIndex,
}) {
  const labelId = `check-action-${peerInstance.id}`;
  return (
    <Tr
      id={`peerInstance-row-${peerInstance.id}`}
      ouiaId={`peerInstance-row-${peerInstance.id}`}
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
        <Link to={`/instances/${peerInstance.instance}/details`}>
          <b>{peerInstance.address}</b>
        </Link>
      </Td>

      <Td id={labelId} dataLabel={t`Port`}>
        <Link to={`/instances/${peerInstance.instance}/details`}>
          <b>{peerInstance.port}</b>
        </Link>
      </Td>

    </Tr>
  );
}

export default InstanceEndPointListItem;
