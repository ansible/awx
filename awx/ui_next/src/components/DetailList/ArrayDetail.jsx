import 'styled-components/macro';
import React from 'react';
import styled from 'styled-components';
import { TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from './Detail';

const Value = styled(DetailValue)`
  margin-top: var(--pf-global--spacer--xs);
  padding: var(--pf-global--spacer--xs);
  border: 1px solid var(--pf-global--BorderColor--100);
  max-height: 5.5em;
  overflow: auto;
`;

function ArrayDetail({ label, value, dataCy }) {
  const labelCy = dataCy ? `${dataCy}-label` : null;
  const valueCy = dataCy ? `${dataCy}-value` : null;

  const vals = Array.isArray(value) ? value : [value];

  return (
    <div css="grid-column: span 2">
      <DetailName component={TextListItemVariants.dt} data-cy={labelCy}>
        {label}
      </DetailName>
      <Value component={TextListItemVariants.dd} data-cy={valueCy}>
        {vals.map(v => (
          <div>{v}</div>
        ))}
      </Value>
    </div>
  );
}

export default ArrayDetail;
