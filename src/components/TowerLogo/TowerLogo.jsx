import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { Brand } from '@patternfly/react-core';

import TowerLogoHeader from '../../../images/tower-logo-header.svg';
import TowerLogoHeaderHover from '../../../images/tower-logo-header-hover.svg';

class TowerLogo extends Component {
  constructor (props) {
    super(props);

    this.state = { hover: false };
  }

  onClick = () => {
    const { history, onClick: handleClick } = this.props;

    if (!handleClick) return;

    history.push('/');

    handleClick();
  };

  onHover = () => {
    const { hover } = this.state;

    this.setState({ hover: !hover });
  };

  render () {
    const { hover } = this.state;
    const { onClick: handleClick } = this.props;

    let src = TowerLogoHeader;

    if (hover && handleClick) {
      src = TowerLogoHeaderHover;
    }

    return (
      <Brand
        src={src}
        alt="Tower Brand Image"
        onMouseOut={this.onHover}
        onMouseOver={this.onHover}
        onBlur={this.onHover}
        onFocus={this.onHover}
        onClick={this.onClick}
      />
    );
  }
}

export default withRouter(TowerLogo);
