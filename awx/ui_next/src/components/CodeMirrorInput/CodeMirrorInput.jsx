import React, { useState, useEffect, useRef, useCallback } from 'react';
import { oneOf, bool, number, string, func } from 'prop-types';
import AceEditor from 'react-ace';
// import * as ace from 'ace-builds';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-yaml';
import 'ace-builds/src-noconflict/theme-github';
import { Controlled as ReactCodeMirror } from 'react-codemirror2';
import styled from 'styled-components';
// import 'codemirror/mode/javascript/javascript';
// import 'codemirror/mode/yaml/yaml';
// import 'codemirror/mode/jinja2/jinja2';
// import 'codemirror/lib/codemirror.css';
// import 'codemirror/addon/display/placeholder';
// require("ace/edit_session").EditSession.prototype.$useWorker=false

const LINE_HEIGHT = 24;
const PADDING = 12;

// ace.config.set('basePath', 'path');

const CodeMirror = styled(ReactCodeMirror)`
  && {
    height: initial;
    padding: 0;
  }

  & > .CodeMirror {
    height: ${props =>
      props.fullHeight ? 'auto' : `${props.rows * LINE_HEIGHT + PADDING}px`};
    font-family: var(--pf-global--FontFamily--monospace);
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

  ${props =>
    props.options &&
    props.options.readOnly &&
    `
    &,
    &:hover {
      --pf-c-form-control--BorderBottomColor: var(--pf-global--BorderColor--300);
    }

    .CodeMirror-cursors {
      display: none;
    }

    .CodeMirror-lines {
      cursor: default;
    }

    .CodeMirror-scroll {
      background-color: var(--pf-c-form-control--disabled--BackgroundColor);
    }
  `}
  ${props =>
    props.options &&
    props.options.placeholder &&
    `
    .CodeMirror-empty {
      pre.CodeMirror-placeholder {
        color: var(--pf-c-form-control--placeholder--Color);
        height: 100% !important;
      }
    }
  `}
`;

function CodeMirrorInput({
  id,
  value,
  onChange,
  mode,
  readOnly,
  hasErrors,
  rows,
  fullHeight,
  className,
  placeholder,
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
    if (wrapper.current === document.activeElement && event.key === 'Enter') {
      const editorInput = editor.current.refEditor?.querySelector('textarea');
      if (editorInput) {
        editorInput.focus();
      }
    }
  }, []);

  useEffect(function addKeyEventListeners() {
    const wrapperEl = wrapper.current;
    wrapperEl.addEventListener('keydown', listen);

    return () => {
      wrapperEl.removeEventListener('keydown', listen);
    };
  });

  return (
    <>
      {/* <CodeMirror
        className={`pf-c-form-control ${className}`}
        value={value}
        onBeforeChange={(editor, data, val) => onChange(val)}
        mode={mode}
        hasErrors={hasErrors}
        options={{
          smartIndent: false,
          lineNumbers: true,
          lineWrapping: true,
          placeholder,
          readOnly,
        }}
        fullHeight={fullHeight}
        rows={rows}
      /> */}
      <div ref={wrapper} tabIndex={0}>
        <AceEditor
          mode={mode === 'javascript' ? 'json' : mode}
          theme="github"
          onChange={onChange}
          value={value}
          name={id || 'code-editor'}
          editorProps={{ $blockScrolling: true }}
          width="100%"
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
    </>
  );
}
CodeMirrorInput.propTypes = {
  value: string.isRequired,
  onChange: func,
  mode: oneOf(['javascript', 'yaml', 'jinja2']).isRequired,
  readOnly: bool,
  hasErrors: bool,
  fullHeight: bool,
  rows: number,
  className: string,
};
CodeMirrorInput.defaultProps = {
  readOnly: false,
  onChange: () => {},
  rows: 6,
  fullHeight: false,
  hasErrors: false,
  className: '',
};

export default CodeMirrorInput;
