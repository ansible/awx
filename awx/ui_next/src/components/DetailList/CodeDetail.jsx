import 'styled-components/macro';
import React from 'react';
import { shape, node, number, oneOf } from 'prop-types';
import { TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from './Detail';
import CodeMirrorInput from '../CodeMirrorInput';

function CodeDetail({ value, label, mode, rows, fullHeight }) {
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
          mode={mode}
          value={value}
          readOnly
          rows={rows}
          fullHeight={fullHeight}
          css="margin-top: 10px"
        />
      </DetailValue>
    </>
  );
}
CodeDetail.propTypes = {
  value: shape.isRequired,
  label: node.isRequired,
  rows: number,
  mode: oneOf(['json', 'yaml', 'jinja2']).isRequired,
};
CodeDetail.defaultProps = {
  rows: null,
};

export default CodeDetail;
