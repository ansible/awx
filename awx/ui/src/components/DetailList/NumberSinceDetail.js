import React from 'react';
import { node, string } from 'prop-types';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import _Detail from './Detail';

const Detail = styled(_Detail)`
  word-break: break-word;
`;

function NumberSinceDetail({ label, number, date, dataCy = null }) {
  return (
    <Detail label={label} dataCy={dataCy} value={t`${number} since ${date}`} />
  );
}
NumberSinceDetail.propTypes = {
  label: node.isRequired,
  number: string.isRequired,
  date: string.isRequired,
};

export default NumberSinceDetail;
