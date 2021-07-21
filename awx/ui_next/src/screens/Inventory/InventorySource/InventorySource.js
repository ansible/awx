import React, { useEffect, useCallback } from 'react';

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
import useRequest from 'hooks/useRequest';

import { InventoriesAPI, InventorySourcesAPI, OrganizationsAPI } from 'api';
import { Schedules } from 'components/Schedule';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import RoutedTabs from 'components/RoutedTabs';
import NotificationList from 'components/NotificationList/NotificationList';
import InventorySourceDetail from '../InventorySourceDetail';
import InventorySourceEdit from '../InventorySourceEdit';

function InventorySource({ inventory, setBreadcrumb, me }) {
  const location = useLocation();
  const match = useRouteMatch('/inventories/inventory/:id/sources/:sourceId');
  const sourceListUrl = `/inventories/inventory/${inventory.id}/sources`;

  const {
    result: { source, isNotifAdmin },
    error,
    isLoading,
    request: fetchSource,
  } = useRequest(
    useCallback(async () => {
      const [inventorySource, notifAdminRes] = await Promise.all([
        InventoriesAPI.readSourceDetail(inventory.id, match.params.sourceId),
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
      ]);
      return {
        source: inventorySource,
        isNotifAdmin: notifAdminRes.data.results.length > 0,
      };
    }, [inventory.id, match.params.sourceId]),
    { source: null, isNotifAdmin: false }
  );

  useEffect(() => {
    fetchSource();
  }, [fetchSource, location.pathname]);

  useEffect(() => {
    if (inventory && source) {
      setBreadcrumb(inventory, source);
    }
  }, [inventory, source, setBreadcrumb]);

  const loadSchedules = useCallback(
    (params) => InventorySourcesAPI.readSchedules(source?.id, params),
    [source]
  );

  const loadScheduleOptions = useCallback(
    () => InventorySourcesAPI.readScheduleOptions(source?.id),
    [source]
  );

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Sources`}
        </>
      ),
      link: `${sourceListUrl}`,
      id: 0,
    },
    {
      name: t`Details`,
      link: `${match.url}/details`,
      id: 1,
    },
    {
      name: t`Schedules`,
      link: `${match.url}/schedules`,
      id: 2,
    },
  ];

  const canToggleNotifications = isNotifAdmin;
  const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: t`Notifications`,
      link: `${match.url}/notifications`,
      id: 3,
    });
  }

  if (error) {
    return <ContentError error={error} />;
  }

  let showCardHeader = true;

  if (['edit', 'schedules/'].some((name) => location.pathname.includes(name))) {
    showCardHeader = false;
  }

  return (
    <>
      {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}

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
          <Route
            key="notifications"
            path="/inventories/inventory/:id/sources/:sourceId/notifications"
          >
            <NotificationList
              id={Number(match.params.sourceId)}
              canToggleNotifications={canToggleNotifications}
              apiModel={InventorySourcesAPI}
            />
          </Route>
          <Route
            key="schedules"
            path="/inventories/inventory/:id/sources/:sourceId/schedules"
          >
            <Schedules
              apiModel={InventorySourcesAPI}
              setBreadcrumb={(schedule) =>
                setBreadcrumb(inventory, source, schedule)
              }
              resource={source}
              loadSchedules={loadSchedules}
              loadScheduleOptions={loadScheduleOptions}
            />
          </Route>
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${match.url}/details`}>
                {t`View inventory source details`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default InventorySource;
