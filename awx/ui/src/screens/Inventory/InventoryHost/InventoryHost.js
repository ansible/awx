import React, { useEffect, useCallback } from 'react';

import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useRouteMatch,
  useLocation,
  useParams,
} from 'react-router-dom';
import { Card } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import useRequest from 'hooks/useRequest';

import { InventoriesAPI } from 'api';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import RoutedTabs from 'components/RoutedTabs';
import JobList from 'components/JobList';
import InventoryHostDetail from '../InventoryHostDetail';
import InventoryHostEdit from '../InventoryHostEdit';
import InventoryHostFacts from '../InventoryHostFacts';
import InventoryHostGroups from '../InventoryHostGroups';

function InventoryHost({ setBreadcrumb, inventory }) {
  const location = useLocation();
  const { hostId, id: inventoryId, inventoryType } = useParams();
  const match = useRouteMatch('/inventories/:inventoryType/:id/hosts/:hostId');
  const hostListUrl = `/inventories/${inventoryType}/${inventory.id}/hosts`;
  const {
    result: { host },
    error: contentError,
    isLoading,
    request: fetchHost,
  } = useRequest(
    useCallback(async () => {
      const response = await InventoriesAPI.readHostDetail(inventoryId, hostId);
      return {
        host: response,
      };
    }, [inventoryId, hostId]),
    {
      host: null,
    }
  );

  useEffect(() => {
    fetchHost();
  }, [fetchHost, location.pathname]);

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
          {t`Back to Hosts`}
        </>
      ),
      link: `${hostListUrl}`,
      id: 0,
    },
    {
      name: t`Details`,
      link: `${match.url}/details`,
      id: 1,
    },
    {
      name: t`Facts`,
      link: `${match.url}/facts`,
      id: 2,
    },
    {
      name: t`Groups`,
      link: `${match.url}/groups`,
      id: 3,
    },
    {
      name: t`Jobs`,
      link: `${match.url}/jobs`,
      id: 4,
    },
  ];

  if (contentError) {
    return (
      <Card>
        <ContentError error={contentError}>
          {contentError.response && contentError.response.status === 404 && (
            <span>
              {t`Host not found.`}{' '}
              <Link to={hostListUrl}>{t`View all Inventory Hosts.`}</Link>
            </span>
          )}
        </ContentError>
      </Card>
    );
  }

  let showCardHeader = true;
  if (['edit'].some((name) => location.pathname.includes(name))) {
    showCardHeader = false;
  }

  return (
    <>
      {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}

      {isLoading && <ContentLoading />}

      {!isLoading && host && (
        <Switch>
          <Redirect
            from="/inventories/:inventoryType/:id/hosts/:hostId"
            to="/inventories/:inventoryType/:id/hosts/:hostId/details"
            exact
          />
          <Route
            key="details"
            path="/inventories/:inventoryType/:id/hosts/:hostId/details"
          >
            <InventoryHostDetail host={host} />
          </Route>
          <Route
            key="edit"
            path="/inventories/:inventoryType/:id/hosts/:hostId/edit"
          >
            <InventoryHostEdit host={host} inventory={inventory} />
          </Route>
          <Route
            key="facts"
            path="/inventories/:inventoryType/:id/hosts/:hostId/facts"
          >
            <InventoryHostFacts host={host} />
          </Route>
          <Route
            key="groups"
            path="/inventories/:inventoryType/:id/hosts/:hostId/groups"
          >
            <InventoryHostGroups />
          </Route>
          <Route
            key="jobs"
            path="/inventories/:inventoryType/:id/hosts/:hostId/jobs"
          >
            <JobList defaultParams={{ job__hosts: host.id }} />
          </Route>
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${match.url}/details`}>
                {t`View Inventory Host Details`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default InventoryHost;
