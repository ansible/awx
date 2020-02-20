import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useRouteMatch,
  useLocation,
} from 'react-router-dom';
import { Card, CardActions } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';

import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import HostFacts from './HostFacts';
import HostDetail from './HostDetail';
import HostEdit from './HostEdit';
import HostGroups from './HostGroups';
import HostCompletedJobs from './HostCompletedJobs';
import { HostsAPI } from '@api';

function Host({ inventory, i18n, setBreadcrumb }) {
  const [host, setHost] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);

  const location = useLocation();
  const hostsMatch = useRouteMatch('/hosts/:id');
  const inventoriesMatch = useRouteMatch(
    '/inventories/inventory/:id/hosts/:hostId'
  );
  const baseUrl = hostsMatch ? hostsMatch.url : inventoriesMatch.url;
  const hostListUrl = hostsMatch
    ? '/hosts'
    : `/inventories/inventory/${inventoriesMatch.params.id}/hosts`;

  useEffect(() => {
    (async () => {
      setContentError(null);
      setHasContentLoading(true);

      try {
        const hostId = hostsMatch
          ? hostsMatch.params.id
          : inventoriesMatch.params.hostId;
        const { data } = await HostsAPI.readDetail(hostId);
        setHost(data);

        if (hostsMatch) {
          setBreadcrumb(data);
        } else if (inventoriesMatch) {
          setBreadcrumb(inventory, data);
        }
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [location]); // eslint-disable-line react-hooks/exhaustive-deps

  const tabsArray = [
    {
      name: i18n._(t`Details`),
      link: `${baseUrl}/details`,
      id: 0,
    },
    {
      name: i18n._(t`Facts`),
      link: `${baseUrl}/facts`,
      id: 1,
    },
    {
      name: i18n._(t`Groups`),
      link: `${baseUrl}/groups`,
      id: 2,
    },
    {
      name: i18n._(t`Completed Jobs`),
      link: `${baseUrl}/completed_jobs`,
      id: 3,
    },
  ];

  if (inventoriesMatch) {
    tabsArray.unshift({
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Hosts`)}
        </>
      ),
      link: hostListUrl,
      id: 99,
    });
  }

  let cardHeader = (
    <TabbedCardHeader>
      <RoutedTabs tabsArray={tabsArray} />
      <CardActions>
        <CardCloseButton linkTo={hostListUrl} />
      </CardActions>
    </TabbedCardHeader>
  );

  if (location.pathname.endsWith('edit')) {
    cardHeader = null;
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (!hasContentLoading && contentError) {
    return (
      <Card>
        <ContentError error={contentError}>
          {contentError.response && contentError.response.status === 404 && (
            <span>
              {i18n._(`Host not found.`)}{' '}
              <Link to={hostListUrl}>{i18n._(`View all Hosts.`)}</Link>
            </span>
          )}
        </ContentError>
      </Card>
    );
  }

  const redirect = hostsMatch ? (
    <Redirect from="/hosts/:id" to="/hosts/:id/details" exact />
  ) : (
    <Redirect
      from="/inventories/inventory/:id/hosts/:hostId"
      to="/inventories/inventory/:id/hosts/:hostId/details"
      exact
    />
  );

  return (
    <Card>
      {cardHeader}
      <Switch>
        {redirect}
        {host && (
          <Route
            path={[
              '/hosts/:id/details',
              '/inventories/inventory/:id/hosts/:hostId/details',
            ]}
          >
            <HostDetail
              host={host}
              onUpdateHost={newHost => setHost(newHost)}
            />
          </Route>
        )}
        {host && (
          <Route
            path={[
              '/hosts/:id/edit',
              '/inventories/inventory/:id/hosts/:hostId/edit',
            ]}
            render={() => <HostEdit host={host} />}
          />
        )}
        {host && (
          <Route
            path="/hosts/:id/facts"
            render={() => <HostFacts host={host} />}
          />
        )}
        {host && (
          <Route
            path="/hosts/:id/groups"
            render={() => <HostGroups host={host} />}
          />
        )}
        {host && (
          <Route
            path="/hosts/:id/completed_jobs"
            render={() => <HostCompletedJobs host={host} />}
          />
        )}
        <Route
          key="not-found"
          path="*"
          render={() =>
            !hasContentLoading && (
              <ContentError isNotFound>
                <Link to={`${baseUrl}/details`}>
                  {i18n._(`View Host Details`)}
                </Link>
              </ContentError>
            )
          }
        />
      </Switch>
    </Card>
  );
}

export default withI18n()(Host);
export { Host as _Host };
