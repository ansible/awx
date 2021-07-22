import React from 'react';

import { t } from '@lingui/macro';
import { node } from 'prop-types';
import styled from 'styled-components';
import _Detail from './Detail';

const Detail = styled(_Detail)`
  dd& {
    color: red;
  }
`;

function DeletedDetail({ label }) {
  return <Detail label={label} value={t`Deleted`} />;
}

DeletedDetail.propTypes = {
  label: node.isRequired,
};

export default DeletedDetail;
