import React from 'react';
import { CardActions } from '@patternfly/react-core';
import styled from 'styled-components';

const CardActionsWrapper = styled.div`
  margin-top: 20px;
  --pf-c-card__actions--PaddingLeft: 0;
`;

function CardActionsRow({ children }) {
  return (
    <CardActionsWrapper>
      <CardActions>{children}</CardActions>
    </CardActionsWrapper>
  );
}

export default CardActionsRow;
