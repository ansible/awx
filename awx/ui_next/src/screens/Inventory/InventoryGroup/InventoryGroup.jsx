import React, { useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { Switch, Route, withRouter, Link, Redirect } from 'react-router-dom';
import { GroupsAPI } from '@api';
import CardCloseButton from '@components/CardCloseButton';
import RoutedTabs from '@components/RoutedTabs';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { TabbedCardHeader } from '@components/Card';
import InventoryGroupEdit from '../InventoryGroupEdit/InventoryGroupEdit';
import InventoryGroupDetail from '../InventoryGroupDetail/InventoryGroupDetail';

function InventoryGroups({ i18n, match, setBreadcrumb, inventory, history }) {
  const [inventoryGroup, setInventoryGroup] = useState(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [contentError, setContentError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const { data } = await GroupsAPI.readDetail(match.params.groupId);
        setInventoryGroup(data);
        setBreadcrumb(inventory, data);
      } catch (err) {
        setContentError(err);
      } finally {
        setContentLoading(false);
      }
    };

    loadData();
  }, [
    history.location.pathname,
    match.params.groupId,
    inventory,
    setBreadcrumb,
  ]);

  const tabsArray = [
    {
      name: i18n._(t`Return to Groups`),
      link: `/inventories/inventory/${inventory.id}/groups`,
      id: 99,
      isNestedTabs: true,
    },
    {
      name: i18n._(t`Details`),
      link: `/inventories/inventory/${inventory.id}/groups/${inventoryGroup &&
        inventoryGroup.id}/details`,
      id: 0,
    },
    {
      name: i18n._(t`Related Groups`),
      link: `/inventories/inventory/${inventory.id}/groups/${inventoryGroup &&
        inventoryGroup.id}/nested_groups`,
      id: 1,
    },
    {
      name: i18n._(t`Hosts`),
      link: `/inventories/inventory/${inventory.id}/groups/${inventoryGroup &&
        inventoryGroup.id}/nested_hosts`,
      id: 2,
    },
  ];

  // In cases where a user manipulates the url such that they try to navigate to a Inventory Group
  // that is not associated with the Inventory Id in the Url this Content Error is thrown.
  // Inventory Groups have a 1: 1 relationship to Inventories thus their Ids must corrolate.

  if (contentLoading) {
    return <ContentLoading />;
  }

  if (
    inventoryGroup.summary_fields.inventory.id !== parseInt(match.params.id, 10)
  ) {
    return (
      <ContentError>
        {inventoryGroup && (
          <Link to={`/inventories/inventory/${inventory.id}/groups`}>
            {i18n._(t`View Inventory Groups`)}
          </Link>
        )}
      </ContentError>
    );
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  let cardHeader = null;
  if (
    history.location.pathname.includes('groups/') &&
    !history.location.pathname.endsWith('edit')
  ) {
    cardHeader = (
      <TabbedCardHeader>
        <RoutedTabs history={history} tabsArray={tabsArray} />
        <CardCloseButton
          linkTo={`/inventories/inventory/${inventory.id}/groups`}
        />
      </TabbedCardHeader>
    );
  }
  return (
    <>
      {cardHeader}
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
              return <InventoryGroupDetail inventoryGroup={inventoryGroup} />;
            }}
          />,
        ]}
        <Route
          key="not-found"
          path="*"
          render={() => {
            return (
              <ContentError>
                {inventory && (
                  <Link to={`/inventories/inventory/${inventory.id}/details`}>
                    {i18n._(t`View Inventory Details`)}
                  </Link>
                )}
              </ContentError>
            );
          }}
        />
      </Switch>
    </>
  );
}

export { InventoryGroups as _InventoryGroups };
export default withI18n()(withRouter(InventoryGroups));
