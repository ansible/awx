import React, { useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, PageSection } from '@patternfly/react-core';
import {
  Switch,
  useParams,
  useHistory,
  useLocation,
  Route,
  Redirect,
  Link,
} from 'react-router-dom';
import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import CredentialDetail from './CredentialDetail';
import { CredentialsAPI } from '@api';

function Credential({ i18n, setBreadcrumb }) {
  const [credential, setCredential] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const history = useHistory();
  const location = useLocation();
  const { id } = useParams();

  useEffect(() => {
    async function fetchData() {
      try {
        const { data } = await CredentialsAPI.readDetail(id);
        setBreadcrumb(data);
        setCredential(data);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    }
    fetchData();
  }, [id, setBreadcrumb]);

  const tabsArray = [
    { name: i18n._(t`Details`), link: `/credentials/${id}/details`, id: 0 },
    { name: i18n._(t`Access`), link: `/credentials/${id}/access`, id: 1 },
    {
      name: i18n._(t`Notifications`),
      link: `/credentials/${id}/notifications`,
      id: 2,
    },
  ];

  let cardHeader = hasContentLoading ? null : (
    <TabbedCardHeader>
      <RoutedTabs history={history} tabsArray={tabsArray} />
      <CardCloseButton linkTo="/credentials" />
    </TabbedCardHeader>
  );

  if (location.pathname.endsWith('edit') || location.pathname.endsWith('add')) {
    cardHeader = null;
  }

  if (!hasContentLoading && contentError) {
    return (
      <PageSection>
        <Card className="awx-c-card">
          <ContentError error={contentError}>
            {contentError.response && contentError.response.status === 404 && (
              <span>
                {i18n._(`Credential not found.`)}{' '}
                <Link to="/credentials">{i18n._(`View all Credentials.`)}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  return (
    <PageSection>
      <Card className="awx-c-card">
        {cardHeader}
        <Switch>
          <Redirect
            from="/credentials/:id"
            to="/credentials/:id/details"
            exact
          />
          {credential && (
            <Route path="/credentials/:id/details">
              <CredentialDetail credential={credential} />
            </Route>
          )}
          <Route
            key="not-found"
            path="*"
            render={() =>
              !hasContentLoading && (
                <ContentError isNotFound>
                  {id && (
                    <Link to={`/credentials/${id}/details`}>
                      {i18n._(`View Credential Details`)}
                    </Link>
                  )}
                </ContentError>
              )
            }
          />
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Credential);
