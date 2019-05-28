import React from 'react';
import PropTypes from 'prop-types';

import { Chip as PFChip } from '@patternfly/react-core';
import styled from 'styled-components';

const Chip = styled(PFChip)`
  padding: 3px 8px;
  height: 24px;
  margin-right: 10px;
  margin-bottom: 10px;

  &.pf-c-chip {
    margin-top: 0;
  }

  &.pf-m-overflow {
    padding: 0;
  }

  &:not(.pf-m-overflow) .pf-c-button {
    display: none;
  }
`;
const BasicChip = ({ children, onToggle, isOverflowChip }) => (
  <Chip
    className="awx-c-chip--basic"
    onClick={onToggle}
    isOverflowChip={isOverflowChip}
  >
    {children}
  </Chip>
);

BasicChip.propTypes = {
  children: PropTypes.node.isRequired,
};

export default BasicChip;
