import React, { Component, Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, withRouter, Switch } from 'react-router-dom';
import { NetworkProvider } from '../../contexts/Network';
import { withRootDialog } from '../../contexts/RootDialog';

import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import TemplatesList from './TemplatesList';

class Templates extends Component {
  constructor (props) {
    super(props);
    const { i18n } = this.props;

    this.state = {
      breadcrumbConfig: {
        '/templates': i18n._(t`Templates`)
      }
    };
  }

  render () {
    const { match, history, setRootDialogMessage, i18n } = this.props;
    const { breadcrumbConfig } = this.state;
    return (
      <Fragment>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route
            path={`${match.path}/:templateType/:id`}
            render={({ match: newRouteMatch }) => (
              <NetworkProvider
                handle404={() => {
                  history.replace('/templates');
                  setRootDialogMessage({
                    title: '404',
                    bodyText: (
                      <Fragment>
                        {i18n._(t`Cannot find template with ID`)}
                        <strong>{` ${newRouteMatch.params.id}`}</strong>
                      </Fragment>
                    ),
                    variant: 'warning'
                  });
                }}
              />
            )}
          />
          <Route
            path={`${match.path}`}
            render={() => (
              <TemplatesList />
            )}
          />
        </Switch>
      </Fragment>
    );
  }
}

export { Templates as _Templates };
export default withI18n()(withRootDialog(withRouter(Templates)));
