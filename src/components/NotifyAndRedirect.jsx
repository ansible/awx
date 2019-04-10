import React, { Component } from 'react';

import { Redirect, withRouter } from 'react-router-dom';

import { Trans } from '@lingui/macro';

import { withRootDialog } from '../contexts/RootDialog';

class NotifyAndRedirect extends Component {
  constructor (props) {
    super(props);

    const { setRootDialogMessage, location } = this.props;
    setRootDialogMessage({
      title: '404',
      bodyText: (
        <Trans>
          Cannot find route
          <strong>{` ${location.pathname}`}</strong>
          .
        </Trans>
      ),
      variant: 'warning'
    });
  }

  render () {
    const { to, push, from, exact, strict, sensitive } = this.props;

    return (
      <Redirect
        to={to}
        push={push}
        from={from}
        exact={exact}
        strict={strict}
        sensitive={sensitive}
      />
    );
  }
}

export { NotifyAndRedirect as _NotifyAndRedirect };
export default withRootDialog(withRouter(NotifyAndRedirect));
