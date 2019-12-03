import React, { useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { Switch, Route, withRouter, Link, Redirect } from 'react-router-dom';
import { GroupsAPI } from '@api';

import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';

import InventoryGroupEdit from '../InventoryGroupEdit/InventoryGroupEdit';

import InventoryGroupDetail from '../InventoryGroupDetail/InventoryGroupDetail';

function InventoryGroups({ i18n, match, setBreadcrumb, inventory }) {
  const [inventoryGroup, setInventoryGroup] = useState(null);
  const [hasContentLoading, setContentLoading] = useState(true);
  const [hasContentError, setHasContentError] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const { data } = await GroupsAPI.readDetail(match.params.groupId);
        setInventoryGroup(data);
        setBreadcrumb(inventory, data);
      } catch (err) {
        setHasContentError(err);
      } finally {
        setContentLoading(false);
      }
    };

    loadData();
  }, [match.params.groupId, setBreadcrumb, inventory]);

  if (hasContentError) {
    return <ContentError />;
  }
  if (hasContentLoading) {
    return <ContentLoading />;
  }
  return (
    <Switch>
      <Redirect
        from="/inventories/inventory/:id/groups/:groupId"
        to="/inventories/inventory/:id/groups/:groupId/details"
        exact
      />
      {inventoryGroup && [
        <Route
          key="edit"
          path="/inventories/inventory/:id/groups/:groupId/edit"
          render={() => {
            return (
              <InventoryGroupEdit
                inventory={inventory}
                inventoryGroup={inventoryGroup}
              />
            );
          }}
        />,
        <Route
          key="details"
          path="/inventories/inventory/:id/groups/:groupId/details"
          render={() => {
            return (
              <InventoryGroupDetail
                inventory={inventory}
                inventoryGroup={inventoryGroup}
              />
            );
          }}
        />,
        <Route
          key="not-found"
          path="*"
          render={() =>
            !hasContentLoading && (
              <ContentError>
                {match.params.id && (
                  <Link
                    to={`/inventories/inventory/${match.params.id}/details`}
                  >
                    {i18n._(t`View Inventory Details`)}
                  </Link>
                )}
              </ContentError>
            )
          }
        />,
      ]}
    </Switch>
  );
}

export { InventoryGroups as _InventoryGroups };
export default withI18n()(withRouter(InventoryGroups));
