import React from 'react';
import { node } from 'prop-types';
import styled from 'styled-components';
import { Badge } from '@patternfly/react-core';

import _Detail from './Detail';

const Detail = styled(_Detail)`
  word-break: break-word;
`;

function DetailBadge({ label, content, dataCy = null }) {
  return (
    <Detail
      label={label}
      dataCy={dataCy}
      value={<Badge isRead>{content}</Badge>}
    />
  );
}
DetailBadge.propTypes = {
  label: node.isRequired,
  content: node.isRequired,
};

export default DetailBadge;
