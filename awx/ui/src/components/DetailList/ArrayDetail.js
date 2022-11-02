import 'styled-components/macro';
import React from 'react';
import styled from 'styled-components';
import { TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from './Detail';
import Popover from '../Popover';

const Value = styled(DetailValue)`
  margin-top: var(--pf-global--spacer--xs);
  padding: var(--pf-global--spacer--xs);
  border: 1px solid var(--pf-global--BorderColor--100);
  max-height: 5.5em;
  overflow: auto;
`;

function ArrayDetail({ label, helpText, value, dataCy }) {
  const labelCy = dataCy ? `${dataCy}-label` : null;
  const valueCy = dataCy ? `${dataCy}-value` : null;

  const vals = Array.isArray(value) ? value : [value];

  return (
    <div css="grid-column: span 2">
      <DetailName component={TextListItemVariants.dt} data-cy={labelCy}>
        {label}
        {helpText && <Popover header={label} content={helpText} id={dataCy} />}
      </DetailName>
      <Value component={TextListItemVariants.dd} data-cy={valueCy}>
        {vals.map((v) => (
          <div key={v}>{v}</div>
        ))}
      </Value>
    </div>
  );
}

export default ArrayDetail;
