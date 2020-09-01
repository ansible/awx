import React, { useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, Redirect, Route, Switch, useRouteMatch } from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import RoutedTabs from '../../../components/RoutedTabs';
import SmartInventoryHostDetail from '../SmartInventoryHostDetail';
import useRequest from '../../../util/useRequest';
import { InventoriesAPI } from '../../../api';

function SmartInventoryHost({ i18n, inventory, setBreadcrumb }) {
  const { params, path, url } = useRouteMatch(
    '/inventories/smart_inventory/:id/hosts/:hostId'
  );

  const { result: host, error, isLoading, request: fetchHost } = useRequest(
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
          {i18n._(t`Back to Hosts`)}
        </>
      ),
      link: `/inventories/smart_inventory/${inventory.id}/hosts`,
      id: 0,
    },
    {
      name: i18n._(t`Details`),
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
                {i18n._(t`View smart inventory host details`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default withI18n()(SmartInventoryHost);
