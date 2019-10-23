import React from 'react';
import PropTypes from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { CopyIcon } from '@patternfly/react-icons';

import styled from 'styled-components';

const CopyButton = styled(Button)`
  padding: 2px 4px;
  margin-left: 8px;
  border: none;
  &:hover {
    background-color: #0066cc;
    color: white;
  }
`;

export const clipboardCopyFunc = (event, text) => {
  const clipboard = event.currentTarget.parentElement;
  const el = document.createElement('input');
  el.value = text;
  clipboard.appendChild(el);
  el.select();
  document.execCommand('copy');
  clipboard.removeChild(el);
};

class ClipboardCopyButton extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      copied: false,
    };

    this.handleCopyClick = this.handleCopyClick.bind(this);
  }

  handleCopyClick = event => {
    const { stringToCopy, switchDelay } = this.props;
    if (this.timer) {
      window.clearTimeout(this.timer);
      this.setState({ copied: false });
    }
    clipboardCopyFunc(event, stringToCopy);
    this.setState({ copied: true }, () => {
      this.timer = window.setTimeout(() => {
        this.setState({ copied: false });
        this.timer = null;
      }, switchDelay);
    });
  };

  render() {
    const { clickTip, entryDelay, exitDelay, hoverTip } = this.props;
    const { copied } = this.state;

    return (
      <Tooltip
        entryDelay={entryDelay}
        exitDelay={exitDelay}
        trigger="mouseenter focus click"
        content={copied ? clickTip : hoverTip}
      >
        <CopyButton
          variant="plain"
          onClick={this.handleCopyClick}
          aria-label={hoverTip}
        >
          <CopyIcon />
        </CopyButton>
      </Tooltip>
    );
  }
}

ClipboardCopyButton.propTypes = {
  clickTip: PropTypes.string.isRequired,
  entryDelay: PropTypes.number,
  exitDelay: PropTypes.number,
  hoverTip: PropTypes.string.isRequired,
  stringToCopy: PropTypes.string.isRequired,
  switchDelay: PropTypes.number,
};

ClipboardCopyButton.defaultProps = {
  entryDelay: 100,
  exitDelay: 1600,
  switchDelay: 2000,
};

export default ClipboardCopyButton;
