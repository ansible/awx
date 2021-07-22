import React, { useEffect, useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, Redirect, Route, Switch, useRouteMatch } from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import RoutedTabs from 'components/RoutedTabs';
import useRequest from 'hooks/useRequest';
import { InventoriesAPI } from 'api';
import SmartInventoryHostDetail from '../SmartInventoryHostDetail';

function SmartInventoryHost({ inventory, setBreadcrumb }) {
  const { params, path, url } = useRouteMatch(
    '/inventories/smart_inventory/:id/hosts/:hostId'
  );

  const {
    result: host,
    error,
    isLoading,
    request: fetchHost,
  } = useRequest(
    useCallback(async () => {
      const response = await InventoriesAPI.readHostDetail(
        inventory.id,
        params.hostId
      );
      return response;
    }, [inventory.id, params.hostId]),
    null
  );

  useEffect(() => {
    fetchHost();
  }, [fetchHost]);

  useEffect(() => {
    if (inventory && host) {
      setBreadcrumb(inventory, host);
    }
  }, [inventory, host, setBreadcrumb]);

  if (error) {
    return <ContentError error={error} />;
  }

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Hosts`}
        </>
      ),
      link: `/inventories/smart_inventory/${inventory.id}/hosts`,
      id: 0,
    },
    {
      name: t`Details`,
      link: `${url}/details`,
      id: 1,
    },
  ];

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />

      {isLoading && <ContentLoading />}

      {!isLoading && host && (
        <Switch>
          <Redirect
            from="/inventories/smart_inventory/:id/hosts/:hostId"
            to={`${path}/details`}
            exact
          />
          <Route key="details" path={`${path}/details`}>
            <SmartInventoryHostDetail host={host} />
          </Route>
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${url}/details`}>
                {t`View smart inventory host details`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default SmartInventoryHost;
