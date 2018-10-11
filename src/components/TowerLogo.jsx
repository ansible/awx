import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { Brand } from '@patternfly/react-core';

import TowerLogoHeader from './tower-logo-header.svg';
import TowerLogoHeaderHover from './tower-logo-header-hover.svg';

class TowerLogo extends Component {
  constructor (props) {
    super(props);

    this.state = { hover: false };
  }

  onClick = () => {
    const { history } = this.props;

    history.push('/');
  };

  onHover = () => {
    const { hover } = this.state;

    this.setState({ hover: !hover });
  };

  render () {
    const { hover } = this.state;

    let src = TowerLogoHeader;

    if (hover) {
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
