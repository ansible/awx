import React, { useEffect, useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, Redirect, Route, Switch, useRouteMatch } from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import RoutedTabs from 'components/RoutedTabs';
import useRequest from 'hooks/useRequest';
import { InventoriesAPI } from 'api';
import AdvancedInventoryHostDetail from '../AdvancedInventoryHostDetail';

function AdvancedInventoryHost({ inventory, setBreadcrumb }) {
  const { params, path, url } = useRouteMatch(
    '/inventories/:inventoryType/:id/hosts/:hostId'
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
    { isLoading: true }
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
      link: `/inventories/${params.inventoryType}/${inventory.id}/hosts`,
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
            from="/inventories/:inventoryType/:id/hosts/:hostId"
            to={`${path}/details`}
            exact
          />
          <Route key="details" path={`${path}/details`}>
            <AdvancedInventoryHostDetail host={host} />
          </Route>
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${url}/details`}>
                {params.inventoryType === 'smart_inventory'
                  ? t`View smart inventory host details`
                  : t`View constructed inventory host details`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default AdvancedInventoryHost;
