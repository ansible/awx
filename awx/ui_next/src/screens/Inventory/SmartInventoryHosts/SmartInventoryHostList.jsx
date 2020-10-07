import React, { useEffect, useCallback, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Tooltip,
  DropdownItem,
  ToolbarItem,
} from '@patternfly/react-core';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';
import SmartInventoryHostListItem from './SmartInventoryHostListItem';
import useRequest from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { InventoriesAPI, CredentialTypesAPI } from '../../../api';
import { Inventory } from '../../../types';
import { Kebabified } from '../../../contexts/Kebabified';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function SmartInventoryHostList({ i18n, inventory }) {
  const location = useLocation();
  const [isAdHocCommandsOpen, setIsAdHocCommandsOpen] = useState(false);

  const {
    result: { hosts, count, moduleOptions, credentialTypeId, isAdHocDisabled },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [hostResponse, adHocOptions, cred] = await Promise.all([
        InventoriesAPI.readHosts(inventory.id, params),
        InventoriesAPI.readAdHocOptions(inventory.id),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
      ]);

      return {
        hosts: hostResponse.data.results,
        count: hostResponse.data.count,
        moduleOptions: adHocOptions.data.actions.GET.module_name.choices,
        credentialTypeId: cred.data.results[0].id,
        isAdHocDisabled: !adHocOptions.data.actions.POST,
      };
    }, [location.search, inventory.id]),
    {
      hosts: [],
      count: 0,
      moduleOptions: [],
      isAdHocDisabled: true,
    }
  );

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    hosts
  );

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={hosts}
        itemCount={count}
        pluralizedItemName={i18n._(t`Hosts`)}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
            isDefault: true,
          },
          {
            name: i18n._(t`Created by (username)`),
            key: 'created_by__username',
          },
          {
            name: i18n._(t`Modified by (username)`),
            key: 'modified_by__username',
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
          },
        ]}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...hosts] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={
              inventory?.summary_fields?.user_capabilities?.adhoc
                ? [
                    <Kebabified>
                      {({ isKebabified }) =>
                        isKebabified ? (
                          <DropdownItem
                            aria-label={i18n._(t`Run command`)}
                            onClick={() => setIsAdHocCommandsOpen(true)}
                            isDisabled={count === 0 || isAdHocDisabled}
                          >
                            {i18n._(t`Run command`)}
                          </DropdownItem>
                        ) : (
                          <ToolbarItem>
                            <Tooltip
                              content={i18n._(
                                t`Select an inventory source by clicking the check box beside it. The inventory source can be a single host or a selection of multiple hosts.`
                              )}
                              position="top"
                              key="adhoc"
                            >
                              <Button
                                variant="secondary"
                                aria-label={i18n._(t`Run command`)}
                                onClick={() => setIsAdHocCommandsOpen(true)}
                                isDisabled={count === 0 || isAdHocDisabled}
                              >
                                {i18n._(t`Run command`)}
                              </Button>
                            </Tooltip>
                          </ToolbarItem>
                        )
                      }
                    </Kebabified>,
                  ]
                : []
            }
          />
        )}
        renderItem={host => (
          <SmartInventoryHostListItem
            key={host.id}
            host={host}
            detailUrl={`/inventories/smart_inventory/${inventory.id}/hosts/${host.id}/details`}
            isSelected={selected.some(row => row.id === host.id)}
            onSelect={() => handleSelect(host)}
          />
        )}
      />
      {isAdHocCommandsOpen && (
        <AdHocCommands
          css="margin-right: 20px"
          adHocItems={selected}
          itemId={parseInt(inventory.id, 10)}
          onClose={() => setIsAdHocCommandsOpen(false)}
          credentialTypeId={credentialTypeId}
          moduleOptions={moduleOptions}
        />
      )}
    </>
  );
}

SmartInventoryHostList.propTypes = {
  inventory: Inventory.isRequired,
};

export default withI18n()(SmartInventoryHostList);
