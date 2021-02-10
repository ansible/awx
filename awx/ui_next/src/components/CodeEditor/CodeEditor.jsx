import React, { useEffect, useRef, useCallback } from 'react';
import { oneOf, bool, number, string, func } from 'prop-types';
import ReactAce from 'react-ace';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-yaml';
import 'ace-builds/src-noconflict/mode-django';
import 'ace-builds/src-noconflict/theme-github';
import styled from 'styled-components';

const LINE_HEIGHT = 24;
const PADDING = 12;

const AceEditor = styled(ReactAce)`
  font-family: var(--pf-global--FontFamily--monospace);
  max-height: 90vh;

  & .ace_gutter,
  & .ace_scroller {
    padding-top: 4px;
    padding-bottom: 4px;
  }

  ${props =>
    props.hasErrors &&
    `
    && {
      --pf-c-form-control--PaddingRight: var(--pf-c-form-control--invalid--PaddingRight);
      --pf-c-form-control--BorderBottomColor: var(--pf-c-form-control--invalid--BorderBottomColor);
      padding-right: 24px;
      padding-bottom: var(--pf-c-form-control--invalid--PaddingBottom);
      background: var(--pf-c-form-control--invalid--Background);
      border-bottom-width: var(--pf-c-form-control--invalid--BorderBottomWidth);
    }`}
`;
AceEditor.displayName = 'AceEditor';

function CodeEditor({
  id,
  value,
  onChange,
  mode,
  readOnly,
  hasErrors,
  rows,
  fullHeight,
  className,
}) {
  const wrapper = useRef(null);
  const editor = useRef(null);

  useEffect(function removeTextareaTabIndex() {
    const editorInput = editor.current.refEditor?.querySelector('textarea');
    if (editorInput) {
      editorInput.tabIndex = -1;
    }
  }, []);

  const listen = useCallback(event => {
    if (
      (wrapper.current === document.activeElement && event.key === 'Enter') ||
      event.key === ' '
    ) {
      const editorInput = editor.current.refEditor?.querySelector('textarea');
      if (!editorInput) {
        return;
      }
      editorInput.focus();
      event.stopPropagation();
    }
  }, []);

  useEffect(function addKeyEventListeners() {
    const wrapperEl = wrapper.current;
    wrapperEl.addEventListener('keydown', listen);

    return () => {
      wrapperEl.removeEventListener('keydown', listen);
    };
  });

  const aceModes = {
    javascript: 'json',
    yaml: 'yaml',
    jinja2: 'django',
  };

  const numRows = fullHeight ? value.split('\n').length : rows;

  return (
    /* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */
    <div ref={wrapper} tabIndex={0}>
      <AceEditor
        mode={aceModes[mode] || 'text'}
        className={`pf-c-form-control ${className}`}
        theme="github"
        onChange={onChange}
        value={value}
        name={id || 'code-editor'}
        editorProps={{ $blockScrolling: true }}
        fontSize={16}
        width="100%"
        height={`${numRows * LINE_HEIGHT + PADDING}px`}
        hasErrors={hasErrors}
        setOptions={{
          readOnly,
          useWorker: false,
        }}
        commands={[
          {
            name: 'escape',
            bindKey: { win: 'Esc', mac: 'Esc' },
            exec: () => {
              wrapper.current.focus();
            },
          },
          {
            name: 'tab escape',
            bindKey: { win: 'Shift-Tab', mac: 'Shift-Tab' },
            exec: () => {
              wrapper.current.focus();
            },
          },
        ]}
        ref={editor}
      />
    </div>
  );
}
CodeEditor.propTypes = {
  value: string.isRequired,
  onChange: func,
  mode: oneOf(['javascript', 'yaml', 'jinja2']).isRequired,
  readOnly: bool,
  hasErrors: bool,
  fullHeight: bool,
  rows: number,
  className: string,
};
CodeEditor.defaultProps = {
  readOnly: false,
  onChange: () => {},
  rows: 6,
  fullHeight: false,
  hasErrors: false,
  className: '',
};

export default CodeEditor;
