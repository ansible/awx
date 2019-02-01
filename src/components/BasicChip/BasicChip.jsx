import React from 'react';
import { Chip } from '@patternfly/react-core';
import './basicChip.scss';

const BasicChip = ({ text }) => (
  <Chip
    className="awx-c-chip--basic"
  >
    {text}
  </Chip>
);

export default BasicChip;
