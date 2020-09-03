import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import TACACSDetail from './TACACSDetail';
import TACACSEdit from './TACACSEdit';

function TACACS({ i18n }) {
  const baseUrl = '/settings/tacacs';

  return (
    <PageSection>
      <Card>
        {i18n._(t`TACACS+ settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <TACACSDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <TACACSEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(TACACS);
