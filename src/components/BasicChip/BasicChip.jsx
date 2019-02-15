import React from 'react';
import PropTypes from 'prop-types';

import { Chip } from '@patternfly/react-core';
import './basicChip.scss';

const BasicChip = ({ text }) => (
  <Chip
    className="awx-c-chip--basic"
  >
    {text}
  </Chip>
);

BasicChip.propTypes = {
  text: PropTypes.string.isRequired,
};

export default BasicChip;
