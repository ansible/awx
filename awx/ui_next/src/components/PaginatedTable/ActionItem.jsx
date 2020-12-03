import 'styled-components/macro';
import React from 'react';
import { Tooltip } from '@patternfly/react-core';

export default function ActionItem({ column, tooltip, visible, children }) {
  if (!visible) {
    return null;
  }

  return (
    <div
      css={`
        grid-column: ${column};
      `}
    >
      <Tooltip content={tooltip} position="top">
        {children}
      </Tooltip>
    </div>
  );
}
