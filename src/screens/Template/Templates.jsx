import React, { Component, Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, withRouter, Switch } from 'react-router-dom';

import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';

import { TemplateList } from './TemplateList';

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
    const { match } = this.props;
    const { breadcrumbConfig } = this.state;
    return (
      <Fragment>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route
            path={`${match.path}`}
            render={() => (
              <TemplateList />
            )}
          />
        </Switch>
      </Fragment>
    );
  }
}

export { Templates as _Templates };
export default withI18n()(withRouter(Templates));
