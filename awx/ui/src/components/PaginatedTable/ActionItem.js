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
      {tooltip ? (
        <Tooltip content={tooltip} position="top">
          <div>{children}</div>
        </Tooltip>
      ) : (
        children
      )}
    </div>
  );
}
