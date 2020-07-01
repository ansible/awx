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
import useRequest from '../../../util/useRequest';

import {
  InventoriesAPI,
  InventorySourcesAPI,
  OrganizationsAPI,
} from '../../../api';
import { Schedules } from '../../../components/Schedule';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import RoutedTabs from '../../../components/RoutedTabs';
import InventorySourceDetail from '../InventorySourceDetail';
import InventorySourceEdit from '../InventorySourceEdit';
import NotificationList from '../../../components/NotificationList/NotificationList';

function InventorySource({ i18n, inventory, setBreadcrumb, me }) {
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

  const loadSchedules = params =>
    InventorySourcesAPI.readSchedules(source?.id, params);

  const createSchedule = data =>
    InventorySourcesAPI.createSchedule(source?.id, data);

  const loadScheduleOptions = () =>
    InventorySourcesAPI.readScheduleOptions(source?.id);

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
      name: i18n._(t`Schedules`),
      link: `${match.url}/schedules`,
      id: 2,
    },
  ];

  const canToggleNotifications = isNotifAdmin;
  const canSeeNotificationsTab = me.is_system_auditor || isNotifAdmin;

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: i18n._(t`Notifications`),
      link: `${match.url}/notifications`,
      id: 3,
    });
  }

  if (error) {
    return <ContentError error={error} />;
  }

  let showCardHeader = true;

  if (['edit', 'schedules/'].some(name => location.pathname.includes(name))) {
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
              createSchedule={createSchedule}
              setBreadcrumb={(unifiedJobTemplate, schedule) =>
                setBreadcrumb(inventory, source, schedule)
              }
              unifiedJobTemplate={source}
              loadSchedules={loadSchedules}
              loadScheduleOptions={loadScheduleOptions}
            />
          </Route>
          <Route key="not-found" path="*">
            <ContentError isNotFound>
              <Link to={`${match.url}/details`}>
                {i18n._(t`View inventory source details`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      )}
    </>
  );
}

export default withI18n()(InventorySource);
