import React, { useCallback, useEffect } from 'react';
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
import { Card, PageSection } from '@patternfly/react-core';

import useRequest from 'hooks/useRequest';
import { InventoriesAPI } from 'api';

import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import JobList from 'components/JobList';
import { ResourceAccessList } from 'components/ResourceAccessList';
import RoutedTabs from 'components/RoutedTabs';
import SmartInventoryDetail from './SmartInventoryDetail';
import SmartInventoryEdit from './SmartInventoryEdit';
import SmartInventoryHosts from './SmartInventoryHosts';

function SmartInventory({ setBreadcrumb }) {
  const location = useLocation();
  const match = useRouteMatch('/inventories/smart_inventory/:id');

  const {
    result: inventory,
    error: contentError,
    isLoading: hasContentLoading,
    request: fetchInventory,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InventoriesAPI.readDetail(match.params.id);
      return data;
    }, [match.params.id]),

    null
  );

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory, location.pathname]);

  useEffect(() => {
    if (inventory) {
      setBreadcrumb(inventory);
    }
  }, [inventory, setBreadcrumb]);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Inventories`}
        </>
      ),
      link: `/inventories`,
      id: 99,
    },
    { name: t`Details`, link: `${match.url}/details`, id: 0 },
    { name: t`Access`, link: `${match.url}/access`, id: 1 },
    { name: t`Hosts`, link: `${match.url}/hosts`, id: 2 },
    {
      name: t`Jobs`,
      link: `${match.url}/jobs`,
      id: 3,
    },
  ];

  if (hasContentLoading) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  if (contentError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={contentError}>
            {contentError?.response?.status === 404 && (
              <span>
                {t`Smart Inventory not found.`}{' '}
                <Link to="/inventories">{t`View all Inventories.`}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  if (inventory?.kind === '') {
    return <Redirect to={`/inventories/inventory/${inventory.id}/details`} />;
  }

  let showCardHeader = true;

  if (['edit', 'hosts/'].some((name) => location.pathname.includes(name))) {
    showCardHeader = false;
  }

  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        <Switch>
          <Redirect
            from="/inventories/smart_inventory/:id"
            to="/inventories/smart_inventory/:id/details"
            exact
          />
          {inventory && [
            <Route
              key="details"
              path="/inventories/smart_inventory/:id/details"
            >
              <SmartInventoryDetail
                isLoading={hasContentLoading}
                inventory={inventory}
              />
            </Route>,
            <Route key="edit" path="/inventories/smart_inventory/:id/edit">
              <SmartInventoryEdit inventory={inventory} />
            </Route>,
            <Route key="access" path="/inventories/smart_inventory/:id/access">
              <ResourceAccessList
                resource={inventory}
                apiModel={InventoriesAPI}
              />
            </Route>,
            <Route key="hosts" path="/inventories/smart_inventory/:id/hosts">
              <SmartInventoryHosts
                inventory={inventory}
                setBreadcrumb={setBreadcrumb}
              />
            </Route>,
            <Route key="jobs" path="/inventories/smart_inventory/:id/jobs">
              <JobList
                defaultParams={{
                  or__job__inventory: inventory.id,
                  or__adhoccommand__inventory: inventory.id,
                  or__inventoryupdate__inventory_source__inventory:
                    inventory.id,
                  or__workflowjob__inventory: inventory.id,
                }}
              />
            </Route>,
            <Route key="not-found" path="*">
              {!hasContentLoading && (
                <ContentError isNotFound>
                  {match.params.id && (
                    <Link
                      to={`/inventories/smart_inventory/${match.params.id}/details`}
                    >
                      {t`View Inventory Details`}
                    </Link>
                  )}
                </ContentError>
              )}
            </Route>,
          ]}
        </Switch>
      </Card>
    </PageSection>
  );
}

export { SmartInventory as _SmartInventory };
export default SmartInventory;
