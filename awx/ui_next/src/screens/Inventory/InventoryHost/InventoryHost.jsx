import React, { useEffect, useCallback } from 'react';
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
import useRequest from '@util/useRequest';

import { HostsAPI } from '@api';
import { Card, CardActions } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { TabbedCardHeader } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import RoutedTabs from '@components/RoutedTabs';
import JobList from '@components/JobList';
import InventoryHostDetail from '../InventoryHostDetail';
import InventoryHostEdit from '../InventoryHostEdit';

function InventoryHost({ i18n, setBreadcrumb, inventory }) {
  const location = useLocation();
  const match = useRouteMatch('/inventories/inventory/:id/hosts/:hostId');
  const hostListUrl = `/inventories/inventory/${inventory.id}/hosts`;

  const {
    result: { host },
    error: contentError,
    isLoading,
    request: fetchHost,
  } = useRequest(
    useCallback(async () => {
      const { data } = await HostsAPI.readDetail(match.params.hostId);

      return {
        host: data,
      };
    }, [match.params.hostId]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      host: null,
    }
  );

  useEffect(() => {
    fetchHost();
  }, [fetchHost]);

  useEffect(() => {
    if (inventory && host) {
      setBreadcrumb(inventory, host);
    }
  }, [inventory, host, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Hosts`)}
        </>
      ),
      link: `${hostListUrl}`,
      id: 0,
    },
    {
      name: i18n._(t`Details`),
      link: `${match.url}/details`,
      id: 1,
    },
    {
      name: i18n._(t`Facts`),
      link: `${match.url}/facts`,
      id: 2,
    },
    {
      name: i18n._(t`Groups`),
      link: `${match.url}/groups`,
      id: 3,
    },
    {
      name: i18n._(t`Completed Jobs`),
      link: `${match.url}/completed_jobs`,
      id: 4,
    },
  ];

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

  if (isLoading) {
    return <ContentLoading />;
  }

  if (!isLoading && contentError) {
    return (
      <Card>
        <ContentError error={contentError}>
          {contentError.response && contentError.response.status === 404 && (
            <span>
              {i18n._(`Host not found.`)}{' '}
              <Link to={hostListUrl}>
                {i18n._(`View all Inventory Hosts.`)}
              </Link>
            </span>
          )}
        </ContentError>
      </Card>
    );
  }

  return (
    <>
      {cardHeader}
      <Switch>
        <Redirect
          from="/inventories/inventory/:id/hosts/:hostId"
          to="/inventories/inventory/:id/hosts/:hostId/details"
          exact
        />
        {host &&
          inventory && [
            <Route
              key="details"
              path="/inventories/inventory/:id/hosts/:hostId/details"
            >
              <InventoryHostDetail host={host} />
            </Route>,
            <Route
              key="edit"
              path="/inventories/inventory/:id/hosts/:hostId/edit"
            >
              <InventoryHostEdit host={host} inventory={inventory} />
            </Route>,
            <Route
              key="completed-jobs"
              path="/inventories/inventory/:id/hosts/:hostId/completed_jobs"
            >
              <JobList defaultParams={{ job__hosts: host.id }} />
            </Route>,
          ]}
        <Route
          key="not-found"
          path="*"
          render={() =>
            !isLoading && (
              <ContentError isNotFound>
                <Link to={`${match.url}/details`}>
                  {i18n._(`View Inventory Host Details`)}
                </Link>
              </ContentError>
            )
          }
        />
      </Switch>
    </>
  );
}

export default withI18n()(InventoryHost);
