import 'styled-components/macro';
import React from 'react';
import {
  arrayOf,
  oneOf,
  oneOfType,
  node,
  number,
  shape,
  string,
} from 'prop-types';
import { TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from './Detail';
import CodeEditor from '../CodeEditor';
import Popover from '../Popover';

function CodeDetail({ value, label, mode, rows, helpText, dataCy }) {
  const labelCy = dataCy ? `${dataCy}-label` : null;
  const valueCy = dataCy ? `${dataCy}-value` : null;
  const editorId = dataCy ? `${dataCy}-editor` : 'code-editor';

  return (
    <>
      <DetailName
        component={TextListItemVariants.dt}
        fullWidth
        css="grid-column: 1 / -1"
        data-cy={labelCy}
      >
        <div className="pf-c-form__label">
          <label
            htmlFor={editorId}
            className="pf-c-form__label-text"
            css="font-weight: var(--pf-global--FontWeight--bold)"
          >
            {label}
          </label>
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
        <CodeEditor
          id={editorId}
          mode={mode}
          value={value}
          readOnly
          rows={rows}
          css="margin-top: 10px"
        />
      </DetailValue>
    </>
  );
}
CodeDetail.propTypes = {
  value: oneOfType([shape({}), arrayOf(string), string]).isRequired,
  label: node.isRequired,
  dataCy: string,
  helpText: string,
  rows: oneOfType([number, string]),
  mode: oneOf(['javascript', 'yaml', 'jinja2']).isRequired,
};
CodeDetail.defaultProps = {
  rows: null,
  helpText: '',
  dataCy: '',
};

export default CodeDetail;
