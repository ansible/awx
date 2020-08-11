import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import RadiusDetail from './RadiusDetail';
import RadiusEdit from './RadiusEdit';

function Radius({ i18n }) {
  const baseUrl = '/settings/radius';

  return (
    <PageSection>
      <Card>
        {i18n._(t`Radius settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <RadiusDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <RadiusEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Radius);
