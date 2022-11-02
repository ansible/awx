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

function DeletedDetail({ label, dataCy, helpText }) {
  return (
    <Detail
      label={label}
      dataCy={dataCy}
      value={t`Deleted`}
      helpText={helpText}
    />
  );
}

DeletedDetail.propTypes = {
  label: node.isRequired,
};

export default DeletedDetail;
