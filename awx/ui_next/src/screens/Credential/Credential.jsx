import React, { useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, PageSection, CardActions } from '@patternfly/react-core';
import {
  Switch,
  useParams,
  useLocation,
  useRouteMatch,
  Route,
  Redirect,
  Link,
} from 'react-router-dom';
import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import { ResourceAccessList } from '@components/ResourceAccessList';
import ContentError from '@components/ContentError';
import RoutedTabs from '@components/RoutedTabs';
import CredentialDetail from './CredentialDetail';
import CredentialEdit from './CredentialEdit';
import { CredentialsAPI } from '@api';

function Credential({ i18n, setBreadcrumb }) {
  const [credential, setCredential] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const { pathname } = useLocation();
  const match = useRouteMatch({
    path: '/credentials/:id',
  });
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
  }, [id, pathname, setBreadcrumb]);

  const tabsArray = [
    { name: i18n._(t`Details`), link: `/credentials/${id}/details`, id: 0 },
  ];

  if (credential && credential.organization) {
    tabsArray.push({
      name: i18n._(t`Access`),
      link: `/credentials/${id}/access`,
      id: 1,
    });
  }

  let cardHeader = hasContentLoading ? null : (
    <TabbedCardHeader>
      <RoutedTabs tabsArray={tabsArray} />
      <CardActions>
        <CardCloseButton linkTo="/credentials" />
      </CardActions>
    </TabbedCardHeader>
  );

  if (pathname.endsWith('edit') || pathname.endsWith('add')) {
    cardHeader = null;
  }

  if (!hasContentLoading && contentError) {
    return (
      <PageSection>
        <Card>
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
      <Card>
        {cardHeader}
        <Switch>
          <Redirect
            from="/credentials/:id"
            to="/credentials/:id/details"
            exact
          />
          {credential && [
            <Route
              key="details"
              path="/credentials/:id/details"
              render={() => <CredentialDetail credential={credential} />}
            />,
            <Route
              key="edit"
              path="/credentials/:id/edit"
              render={() => <CredentialEdit credential={credential} />}
            />,
            credential.organization && (
              <Route
                key="access"
                path="/credentials/:id/access"
                render={() => (
                  <ResourceAccessList
                    resource={credential}
                    apiModel={CredentialsAPI}
                  />
                )}
              />
            ),
            <Route
              key="not-found"
              path="*"
              render={() =>
                !hasContentLoading && (
                  <ContentError isNotFound>
                    {match.params.id && (
                      <Link to={`/credentials/${match.params.id}/details`}>
                        {i18n._(`View Credential Details`)}
                      </Link>
                    )}
                  </ContentError>
                )
              }
            />,
          ]}
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
