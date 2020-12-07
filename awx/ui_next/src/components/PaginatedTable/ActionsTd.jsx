import 'styled-components/macro';
import React from 'react';
import { Td } from '@patternfly/react-table';
import styled, { css } from 'styled-components';

const ActionsGrid = styled.div`
  display: grid;
  grid-gap: 16px;
  align-items: center;

  ${props => {
    const columns = '40px '.repeat(props.numActions || 1);
    return css`
      grid-template-columns: ${columns};
    `;
  }}
`;

export default function ActionsTd({ children }) {
  const numActions = children.length || 1;
  const width = numActions * 40;
  return (
    <Td
      css={`
        text-align: right;
        --pf-c-table--cell--Width: ${width}px;
      `}
    >
      <ActionsGrid numActions={numActions}>
        {React.Children.map(children, (child, i) =>
          React.cloneElement(child, {
            column: i + 1,
          })
        )}
      </ActionsGrid>
    </Td>
  );
}
