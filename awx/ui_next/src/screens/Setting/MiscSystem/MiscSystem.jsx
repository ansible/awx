import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import MiscSystemDetail from './MiscSystemDetail';
import MiscSystemEdit from './MiscSystemEdit';

function MiscSystem({ i18n }) {
  const baseUrl = '/settings/miscellaneous_system';

  return (
    <PageSection>
      <Card>
        {i18n._(t`Miscellaneous system settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <MiscSystemDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <MiscSystemEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(MiscSystem);
