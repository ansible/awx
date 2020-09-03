import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import UIDetail from './UIDetail';
import UIEdit from './UIEdit';

function UI({ i18n }) {
  const baseUrl = '/settings/ui';

  return (
    <PageSection>
      <Card>
        {i18n._(t`User interface settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <UIDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <UIEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(UI);
