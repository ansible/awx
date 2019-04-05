import React from 'react';
import PropTypes from 'prop-types';

import { Chip } from '@patternfly/react-core';
import './basicChip.scss';

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
