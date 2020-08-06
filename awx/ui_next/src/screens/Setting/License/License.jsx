import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import LicenseDetail from './LicenseDetail';
import LicenseEdit from './LicenseEdit';

function License({ i18n }) {
  const baseUrl = '/settings/license';

  return (
    <PageSection>
      <Card>
        {i18n._(t`License settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <LicenseDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <LicenseEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(License);
