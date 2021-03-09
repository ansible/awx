import React, { useEffect, useRef, useCallback, useState } from 'react';
import { oneOf, bool, number, string, func } from 'prop-types';
import ReactAce from 'react-ace';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/mode-yaml';
import 'ace-builds/src-noconflict/mode-django';
import 'ace-builds/src-noconflict/theme-github';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

const LINE_HEIGHT = 24;
const PADDING = 12;

const FocusWrapper = styled.div`
  && + .keyboard-help-text {
    display: none;
  }

  &:focus-within + .keyboard-help-text {
    display: block;
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
  mode,
  readOnly,
  hasErrors,
  rows,
  fullHeight,
  className,
  i18n,
}) {
  const [isKeyboardFocused, setIsKeyboardFocused] = useState(false);
  const wrapper = useRef(null);
  const editor = useRef(null);

  useEffect(
    function removeTextareaTabIndex() {
      const editorInput = editor.current.refEditor?.querySelector('textarea');
      if (editorInput && !readOnly) {
        editorInput.tabIndex = -1;
      }
    },
    [readOnly]
  );

  const listen = useCallback(event => {
    if (
      (wrapper.current === document.activeElement && event.key === 'Enter') ||
      event.key === ' '
    ) {
      const editorInput = editor.current.refEditor?.querySelector('textarea');
      if (!editorInput) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      editorInput.focus();
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
    <>
      <FocusWrapper
        ref={wrapper}
        tabIndex={readOnly ? -1 : 0}
        onFocus={e => {
          if (e.target === e.currentTarget) {
            setIsKeyboardFocused(true);
          }
          if (e.target.className.includes('ace_scrollbar')) {
            setIsKeyboardFocused(false);
          }
        }}
      >
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
            highlightActiveLine: !readOnly,
            highlightGutterLine: !readOnly,
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
      </FocusWrapper>
      {isKeyboardFocused && !readOnly && (
        <div
          className="pf-c-form__helper-text keyboard-help-text"
          aria-live="polite"
        >
          {i18n._(t`Press Enter to edit. Press ESC to stop editing.`)}
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

export default withI18n()(CodeEditor);
