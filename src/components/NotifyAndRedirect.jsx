import React from 'react';

import { Redirect, withRouter } from 'react-router-dom';

import { Trans } from '@lingui/macro';

import { withRootDialog } from '../contexts/RootDialog';

const NotifyAndRedirect = ({
  to,
  push,
  from,
  exact,
  strict,
  sensitive,
  setRootDialogMessage,
  location
}) => {
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
};

export { NotifyAndRedirect as _NotifyAndRedirect };
export default withRootDialog(withRouter(NotifyAndRedirect));
