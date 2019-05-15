import React, { Fragment } from 'react';

import { Redirect, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { withRootDialog } from '../contexts/RootDialog';

const NotifyAndRedirect = ({
  to,
  push,
  from,
  exact,
  strict,
  sensitive,
  setRootDialogMessage,
  location,
  i18n
}) => {
  setRootDialogMessage({
    title: '404',
    bodyText: (
      <Fragment>{i18n._(t`Cannot find route ${(<strong>{location.pathname}</strong>)}.`)}</Fragment>
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
export default withI18n()(withRootDialog(withRouter(NotifyAndRedirect)));
