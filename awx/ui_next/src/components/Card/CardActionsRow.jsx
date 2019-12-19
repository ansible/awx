import React from 'react';
import { CardActions } from '@patternfly/react-core';
import styled from 'styled-components';

const CardActionsWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;

  & > .pf-c-card__actions > :not(:first-child) {
    margin-left: 0.5rem;
  }
`;

function CardActionsRow({ children }) {
  return (
    <CardActionsWrapper>
      <CardActions>{children}</CardActions>
    </CardActionsWrapper>
  );
}

export default CardActionsRow;
