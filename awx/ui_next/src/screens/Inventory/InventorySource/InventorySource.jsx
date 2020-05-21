import React, { useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Link,
  Switch,
  Route,
  Redirect,
  useRouteMatch,
  useLocation,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { CardActions } from '@patternfly/react-core';
import useRequest from '../../../util/useRequest';

import { InventoriesAPI } from '../../../api';
import { TabbedCardHeader } from '../../../components/Card';
import CardCloseButton from '../../../components/CardCloseButton';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import RoutedTabs from '../../../components/RoutedTabs';
import InventorySourceDetail from '../InventorySourceDetail';
import InventorySourceEdit from '../InventorySourceEdit';

function InventorySource({ i18n, inventory, setBreadcrumb }) {
  const location = useLocation();
  const match = useRouteMatch('/inventories/inventory/:id/sources/:sourceId');
  const sourceListUrl = `/inventories/inventory/${inventory.id}/sources`;

  const { result: source, error, isLoading, request: fetchSource } = useRequest(
    useCallback(async () => {
      return InventoriesAPI.readSourceDetail(
        inventory.id,
        match.params.sourceId
      );
    }, [inventory.id, match.params.sourceId]),
    null
  );

  useEffect(() => {
    fetchSource();
  }, [fetchSource, location.pathname]);

  useEffect(() => {
    if (inventory && source) {
      setBreadcrumb(inventory, source);
    }
  }, [inventory, source, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Sources`)}
        </>
      ),
      link: `${sourceListUrl}`,
      id: 0,
    },
    {
      name: i18n._(t`Details`),
      link: `${match.url}/details`,
      id: 1,
    },
    {
      name: i18n._(t`Notifications`),
      link: `${match.url}/notifications`,
      id: 2,
    },
    {
      name: i18n._(t`Schedules`),
      link: `${match.url}/schedules`,
      id: 3,
    },
  ];

  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <>
      {['edit'].some(name => location.pathname.includes(name)) ? null : (
        <TabbedCardHeader>
          <RoutedTabs tabsArray={tabsArray} />
          <CardActions>
            <CardCloseButton linkTo={sourceListUrl} />
          </CardActions>
        </TabbedCardHeader>
      )}

      {isLoading && <ContentLoading />}

      {!isLoading && source && (
        <Switch>
          <Redirect
            from="/inventories/inventory/:id/sources/:sourceId"
            to="/inventories/inventory/:id/sources/:sourceId/details"
            exact
          />
          <Route
            key="details"
            path="/inventories/inventory/:id/sources/:sourceId/details"
          >
            <InventorySourceDetail inventorySource={source} />
          </Route>
          <Route
            key="edit"
            path="/inventories/inventory/:id/sources/:sourceId/edit"
          >
            <InventorySourceEdit source={source} inventory={inventory} />
          </Route>
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${match.url}/details`}>
                {i18n._(`View inventory source details`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default withI18n()(InventorySource);
