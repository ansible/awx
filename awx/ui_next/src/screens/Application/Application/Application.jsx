import React, { useCallback, useEffect } from 'react';
import {
  Route,
  Switch,
  Redirect,
  useParams,
  useLocation,
  Link,
} from 'react-router-dom';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';

import useRequest from '../../../util/useRequest';
import { ApplicationsAPI } from '../../../api';
import ContentError from '../../../components/ContentError';
import ApplicationEdit from '../ApplicationEdit';
import ApplicationDetails from '../ApplicationDetails';
import ApplicationTokens from '../ApplicationTokens';
import RoutedTabs from '../../../components/RoutedTabs';

function Application({ setBreadcrumb, i18n }) {
  const { id } = useParams();
  const { pathname } = useLocation();
  const {
    isLoading,
    error,
    result: { application, authorizationOptions, clientTypeOptions },
    request: fetchApplication,
  } = useRequest(
    useCallback(async () => {
      const [detail, options] = await Promise.all([
        ApplicationsAPI.readDetail(id),
        ApplicationsAPI.readOptions(),
      ]);
      const authorization = options.data.actions.GET.authorization_grant_type.choices.map(
        choice => ({
          value: choice[0],
          label: choice[1],
          key: choice[0],
        })
      );
      const clientType = options.data.actions.GET.client_type.choices.map(
        choice => ({
          value: choice[0],
          label: choice[1],
          key: choice[0],
        })
      );
      setBreadcrumb(detail.data);

      return {
        application: detail.data,
        authorizationOptions: authorization,
        clientTypeOptions: clientType,
      };
    }, [setBreadcrumb, id]),
    { authorizationOptions: [], clientTypeOptions: [] }
  );

  useEffect(() => {
    fetchApplication();
  }, [fetchApplication, pathname]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to applications`)}
        </>
      ),
      link: '/applications',
      id: 0,
    },
    { name: i18n._(t`Details`), link: `/applications/${id}/details`, id: 1 },
    { name: i18n._(t`Tokens`), link: `/applications/${id}/tokens`, id: 2 },
  ];

  let cardHeader = <RoutedTabs tabsArray={tabsArray} />;
  if (pathname.endsWith('edit')) {
    cardHeader = null;
  }

  if (!isLoading && error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error.response?.status === 404 && (
              <span>
                {i18n._(t`Application not found.`)}{' '}
                <Link to="/applications">
                  {i18n._(t`View all applications.`)}
                </Link>
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
            from="/applications/:id"
            to="/applications/:id/details"
            exact
          />
          {application && (
            <>
              <Route path="/applications/:id/edit">
                <ApplicationEdit
                  authorizationOptions={authorizationOptions}
                  clientTypeOptions={clientTypeOptions}
                  application={application}
                />
              </Route>
              <Route path="/applications/:id/details">
                <ApplicationDetails
                  application={application}
                  authorizationOptions={authorizationOptions}
                  clientTypeOptions={clientTypeOptions}
                />
              </Route>
              <Route path="/applications/:id/tokens">
                <ApplicationTokens application={application} />
              </Route>
            </>
          )}
        </Switch>
      </Card>
    </PageSection>
  );
}
export default withI18n()(Application);
