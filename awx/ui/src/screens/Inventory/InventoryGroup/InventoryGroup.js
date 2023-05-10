import React, { useEffect, useState } from 'react';
import { t } from '@lingui/macro';

import {
  Switch,
  Route,
  Link,
  Redirect,
  useLocation,
  useParams,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { GroupsAPI } from 'api';
import InventoryGroupEdit from '../InventoryGroupEdit/InventoryGroupEdit';
import InventoryGroupDetail from '../InventoryGroupDetail/InventoryGroupDetail';
import InventoryGroupHosts from '../InventoryGroupHosts';
import InventoryRelatedGroups from '../InventoryRelatedGroups';

function InventoryGroup({ setBreadcrumb, inventory }) {
  const [inventoryGroup, setInventoryGroup] = useState(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [contentError, setContentError] = useState(null);
  const { id: inventoryId, groupId, inventoryType } = useParams();
  const location = useLocation();

  useEffect(() => {
    const loadData = async () => {
      try {
        const { data } = await GroupsAPI.readDetail(groupId);
        setInventoryGroup(data);
        setBreadcrumb(inventory, data);
      } catch (err) {
        setContentError(err);
      } finally {
        setContentLoading(false);
      }
    };

    loadData();
  }, [location.pathname, groupId, inventory, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon aria-label={t`Back to Groups`} />
          {t`Back to Groups`}
        </>
      ),
      link: `/inventories/${inventoryType}/${inventoryId}/groups`,
      id: 99,
    },
    {
      name: t`Details`,
      link: `/inventories/${inventoryType}/${inventoryId}/groups/${inventoryGroup?.id}/details`,
      id: 0,
    },
    {
      name: t`Related Groups`,
      link: `/inventories/${inventoryType}/${inventoryId}/groups/${inventoryGroup?.id}/nested_groups`,
      id: 1,
    },
    {
      name: t`Hosts`,
      link: `/inventories/${inventoryType}/${inventoryId}/groups/${inventoryGroup?.id}/nested_hosts`,
      id: 2,
    },
  ];

  if (contentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  // In cases where a user manipulates the url such that they try to navigate to a
  // Inventory Group that is not associated with the Inventory Id in the Url this
  // Content Error is thrown. Inventory Groups have a 1:1 relationship to Inventories
  // thus their Ids must corrolate.

  if (
    inventoryGroup?.summary_fields?.inventory?.id !== parseInt(inventoryId, 10)
  ) {
    return (
      <ContentError isNotFound>
        <Link to={`/inventories/inventory/${inventory.id}/groups`}>
          {t`View Inventory Groups`}
        </Link>
      </ContentError>
    );
  }

  let showCardHeader = true;
  if (['add', 'edit'].some((name) => location.pathname.includes(name))) {
    showCardHeader = false;
  }

  return (
    <>
      {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
      <Switch>
        <Redirect
          from="/inventories/:inventoryType/:id/groups/:groupId"
          to="/inventories/:inventoryType/:id/groups/:groupId/details"
          exact
        />
        {inventoryGroup && [
          <Route
            key="edit"
            path="/inventories/:inventoryType/:id/groups/:groupId/edit"
          >
            <InventoryGroupEdit inventoryGroup={inventoryGroup} />
          </Route>,
          <Route
            key="details"
            path="/inventories/:inventoryType/:id/groups/:groupId/details"
          >
            <InventoryGroupDetail inventoryGroup={inventoryGroup} />
          </Route>,
          <Route
            key="hosts"
            path="/inventories/:inventoryType/:id/groups/:groupId/nested_hosts"
          >
            <InventoryGroupHosts inventoryGroup={inventoryGroup} />
          </Route>,
          <Route
            key="relatedGroups"
            path="/inventories/:inventoryType/:id/groups/:groupId/nested_groups"
          >
            <InventoryRelatedGroups />
          </Route>,
        ]}
        <Route key="not-found" path="*">
          <ContentError>
            {inventory && (
              <Link to={`/inventories/:inventoryType/${inventory.id}/details`}>
                {t`View Inventory Details`}
              </Link>
            )}
          </ContentError>
        </Route>
      </Switch>
    </>
  );
}

export { InventoryGroup as _InventoryGroup };
export default InventoryGroup;
