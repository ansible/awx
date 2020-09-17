import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import LDAPDetail from './LDAPDetail';
import LDAPEdit from './LDAPEdit';

function LDAP({ i18n }) {
  const baseURL = '/settings/ldap';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/default/details`} exact />
          <Route path={`${baseURL}/:category/details`}>
            <LDAPDetail />
          </Route>
          <Route path={`${baseURL}/:category/edit`}>
            <LDAPEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/default/details`}>
                {i18n._(t`View LDAP Settings`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(LDAP);
