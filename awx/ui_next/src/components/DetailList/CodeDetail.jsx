import 'styled-components/macro';
import React from 'react';
import { shape, node, number, oneOf, string } from 'prop-types';
import { TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from './Detail';
import CodeMirrorInput from '../CodeMirrorInput';
import Popover from '../Popover';

function CodeDetail({
  value,
  label,
  mode,
  rows,
  fullHeight,
  helpText,
  dataCy,
}) {
  const labelCy = dataCy ? `${dataCy}-label` : null;
  const valueCy = dataCy ? `${dataCy}-value` : null;

  return (
    <>
      <DetailName
        component={TextListItemVariants.dt}
        fullWidth
        css="grid-column: 1 / -1"
        data-cy={labelCy}
      >
        <div className="pf-c-form__label">
          <span
            className="pf-c-form__label-text"
            css="font-weight: var(--pf-global--FontWeight--bold)"
          >
            {label}
          </span>
          {helpText && (
            <Popover header={label} content={helpText} id={dataCy} />
          )}
        </div>
      </DetailName>
      <DetailValue
        component={TextListItemVariants.dd}
        fullWidth
        css="grid-column: 1 / -1; margin-top: -20px"
        data-cy={valueCy}
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
  dataCy: string,
  helpText: string,
  rows: number,
  mode: oneOf(['json', 'yaml', 'jinja2']).isRequired,
};
CodeDetail.defaultProps = {
  rows: null,
  helpText: '',
  dataCy: '',
};

export default CodeDetail;
