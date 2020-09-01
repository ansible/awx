import 'styled-components/macro';
import React from 'react';
import { shape, node, number } from 'prop-types';
import { TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from './Detail';
import CodeMirrorInput from '../CodeMirrorInput';

function ObjectDetail({ value, label, rows, fullHeight }) {
  return (
    <>
      <DetailName
        component={TextListItemVariants.dt}
        fullWidth
        css="grid-column: 1 / -1"
      >
        <div className="pf-c-form__label">
          <span
            className="pf-c-form__label-text"
            css="font-weight: var(--pf-global--FontWeight--bold)"
          >
            {label}
          </span>
        </div>
      </DetailName>
      <DetailValue
        component={TextListItemVariants.dd}
        fullWidth
        css="grid-column: 1 / -1; margin-top: -20px"
      >
        <CodeMirrorInput
          mode="json"
          value={JSON.stringify(value)}
          readOnly
          rows={rows}
          fullHeight={fullHeight}
          css="margin-top: 10px"
        />
      </DetailValue>
    </>
  );
}
ObjectDetail.propTypes = {
  value: shape.isRequired,
  label: node.isRequired,
  rows: number,
};
ObjectDetail.defaultProps = {
  rows: null,
};

export default ObjectDetail;
