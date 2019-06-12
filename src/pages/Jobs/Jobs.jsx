import React, { Component, Fragment } from 'react';
import { Route, withRouter, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { NetworkProvider } from '../../contexts/Network';
import { withRootDialog } from '../../contexts/RootDialog';

import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import Job from './Job';

class Jobs extends Component {
  constructor (props) {
    super(props);

    const { i18n } = props;

    this.state = {
      breadcrumbConfig: {
        '/jobs': i18n._(t`Jobs`)
      }
    }
  }

  setBreadcrumbConfig = (job) => {
    const { i18n } = this.props;

    if (!job) {
      return;
    }

    const breadcrumbConfig = {
      '/jobs': i18n._(`Jobs`),
      [`/jobs/${job.id}`]: `${job.name}`,
      [`/jobs/${job.id}/details`]: i18n._(`Details`),
      [`/jobs/${job.id}/output`]: i18n._(`Output`)
    };

    this.setState({ breadcrumbConfig });
  }

  render () {
    const { match, history, location, setRootDialogMessage, i18n } = this.props;
    const { breadcrumbConfig } = this.state;

    return (
      <Fragment>
        <Breadcrumbs
          breadcrumbConfig={breadcrumbConfig}
        />
        <Switch>
          <Route
            path={`${match.path}/:id`}
            render={({ match: newRouteMatch }) => (
              <NetworkProvider
                handle404={() => {
                  history.replace('/jobs');
                  setRootDialogMessage({
                    title: '404',
                    bodyText: (
                      <Fragment>
                        {i18n._(t`Cannot find job with ID`)}
                        <strong>{` ${newRouteMatch.params.id}`}</strong>
                        .
                      </Fragment>
                    ),
                    variant: 'warning'
                  });
                }}
                >
                <Job
                  history={history}
                  location={location}
                  setBreadcrumb={this.setBreadcrumbConfig}
                />
              </NetworkProvider>
            )}
          />
        </Switch>
      </Fragment>
    );
  }
}

export default withI18n()(withRootDialog(withRouter(Jobs)));
