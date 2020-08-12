import React, { useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import RoutedTabs from '../../../components/RoutedTabs';
import ContentError from '../../../components/ContentError';
import { TokensAPI } from '../../../api';
import useRequest from '../../../util/useRequest';
import UserTokenDetail from '../UserTokenDetail';

function UserToken({ i18n, setBreadcrumb, user }) {
  const location = useLocation();
  const { id, tokenId } = useParams();
  const {
    isLoading,
    error,
    request: fetchToken,
    result: { token, actions },
  } = useRequest(
    useCallback(async () => {
      const [response, actionsResponse] = await Promise.all([
        TokensAPI.readDetail(tokenId),
        TokensAPI.readOptions(),
      ]);
      setBreadcrumb(user, response.data);
      return {
        token: response.data,
        actions: actionsResponse.data.actions.POST,
      };
    }, [setBreadcrumb, user, tokenId]),
    { token: null, actions: null }
  );
  useEffect(() => {
    fetchToken();
  }, [fetchToken]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Tokens`)}
        </>
      ),
      link: `/users/${id}/tokens`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `/users/${id}/tokens/${tokenId}/details`,
      id: 0,
    },
  ];

  let showCardHeader = true;

  if (location.pathname.endsWith('edit')) {
    showCardHeader = false;
  }

  if (!isLoading && error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error.response.status === 404 && (
              <span>
                {i18n._(t`Token not found.`)}{' '}
                <Link to="/users/:id/tokens">
                  {i18n._(t`View all tokens.`)}
                </Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  return (
    <>
      {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
      <Switch>
        <Redirect
          from="/users/:id/tokens/:tokenId"
          to="/users/:id/tokens/:tokenId/details"
          exact
        />
        {token && (
          <Route path="/users/:id/tokens/:tokenId/details">
            <UserTokenDetail canEditOrDelete={actions} token={token} />
          </Route>
        )}
        <Route key="not-found" path="*">
          {!isLoading && (
            <ContentError isNotFound>
              {id && (
                <Link to={`/users/${id}/tokens`}>{i18n._(t`View Tokens`)}</Link>
              )}
            </ContentError>
          )}
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(UserToken);
