import React, { useEffect, useRef, useCallback } from 'react';
import { oneOf, bool, number, string, func, oneOfType } from 'prop-types';

import ReactAce from 'react-ace';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-yaml';
import 'ace-builds/src-noconflict/mode-django';
import 'ace-builds/src-noconflict/theme-github';

import { t } from '@lingui/macro';
import styled from 'styled-components';
import debounce from 'util/debounce';

const LINE_HEIGHT = 24;
const PADDING = 12;

const FocusWrapper = styled.div`
  && + .keyboard-help-text {
    opacity: 0;
    transition: opacity 0.1s linear;
  }

  &:focus-within + .keyboard-help-text {
    opacity: 1;
  }

  & .ace_hidden-cursors .ace_cursor {
    opacity: 0;
  }
`;

const AceEditor = styled(ReactAce)`
  font-family: var(--pf-global--FontFamily--monospace);
  max-height: 90vh;

  & .ace_gutter,
  & .ace_scroller {
    padding-top: 4px;
    padding-bottom: 4px;
  }

  & .ace_mobile-menu {
    display: none;
  }

  ${(props) =>
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

  ${(props) =>
    props.setOptions.readOnly &&
    `
    && .ace_cursor {
      opacity: 0;
    }
    `}
`;
AceEditor.displayName = 'AceEditor';

function CodeEditor({
  id,
  value,
  onChange,
  onFocus,
  onBlur,
  mode,
  readOnly,
  hasErrors,
  rows,
  fullHeight,
  className,
}) {
  if (rows && typeof rows !== 'number' && rows !== 'auto') {
    // eslint-disable-next-line no-console
    console.warn(
      `CodeEditor: Unexpected value for 'rows': ${rows}; expected number or 'auto'`
    );
  }

  const wrapper = useRef(null);
  const editor = useRef(null);

  useEffect(() => {
    const editorInput = editor.current.refEditor?.querySelector('textarea');
    if (!editorInput) {
      return;
    }
    if (!readOnly) {
      editorInput.tabIndex = -1;
    }
    editorInput.id = id;
  }, [readOnly, id]);

  const listen = useCallback((event) => {
    if (wrapper.current === document.activeElement && event.key === 'Enter') {
      const editorInput = editor.current.refEditor?.querySelector('textarea');
      if (!editorInput) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      editorInput.focus();
    }
  }, []);

  useEffect(() => {
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

  const numRows = rows === 'auto' ? value.split('\n').length : rows;
  const height = fullHeight ? '50vh' : `${numRows * LINE_HEIGHT + PADDING}px`;

  return (
    <>
      <FocusWrapper ref={wrapper} tabIndex={readOnly ? -1 : 0}>
        <AceEditor
          mode={aceModes[mode] || 'text'}
          className={`pf-c-form-control ${className}`}
          theme="github"
          onChange={debounce(onChange, 250)}
          value={value}
          onFocus={onFocus}
          onBlur={onBlur}
          name={`${id}-editor` || 'code-editor'}
          editorProps={{ $blockScrolling: true }}
          fontSize={16}
          width="100%"
          height={height}
          hasErrors={hasErrors}
          setOptions={{
            readOnly,
            highlightActiveLine: !readOnly,
            highlightGutterLine: !readOnly,
            useWorker: false,
            showPrintMargin: false,
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
      </FocusWrapper>
      {!readOnly && (
        <div
          className="pf-c-form__helper-text keyboard-help-text"
          aria-live="polite"
        >
          {t`Press Enter to edit. Press ESC to stop editing.`}
        </div>
      )}
    </>
  );
}
CodeEditor.propTypes = {
  value: string.isRequired,
  onChange: func,
  mode: oneOf(['javascript', 'yaml', 'jinja2']).isRequired,
  readOnly: bool,
  hasErrors: bool,
  fullHeight: bool,
  rows: oneOfType([number, string]),
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
