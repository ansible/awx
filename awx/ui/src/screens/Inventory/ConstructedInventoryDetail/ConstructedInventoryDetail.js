import React, { useCallback, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import {
  Button,
  Chip,
  TextList,
  TextListItem,
  TextListItemVariants,
  TextListVariants,
} from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import { VariablesDetail } from 'components/CodeEditor';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import ChipGroup from 'components/ChipGroup';
import Popover from 'components/Popover';
import { InventoriesAPI, ConstructedInventoriesAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { Inventory } from 'types';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import InstanceGroupLabels from 'components/InstanceGroupLabels';
import getHelpText from '../shared/Inventory.helptext';

function ConstructedInventoryDetail({ inventory }) {
  const history = useHistory();
  const helpText = getHelpText();

  const {
    result: { instanceGroups, sourceInventories, actions },
    request: fetchRelatedDetails,
    error: contentError,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const [response, sourceInvResponse, options] = await Promise.all([
        InventoriesAPI.readInstanceGroups(inventory.id),
        InventoriesAPI.readSourceInventories(inventory.id),
        ConstructedInventoriesAPI.readOptions(inventory.id),
      ]);

      return {
        instanceGroups: response.data.results,
        sourceInventories: sourceInvResponse.data.results,
        actions: options.data.actions.GET,
      };
    }, [inventory.id]),
    {
      instanceGroups: [],
      sourceInventories: [],
      actions: {},
      isLoading: true,
    }
  );

  useEffect(() => {
    fetchRelatedDetails();
  }, [fetchRelatedDetails]);

  const { request: deleteInventory, error: deleteError } = useRequest(
    useCallback(async () => {
      await InventoriesAPI.destroy(inventory.id);
      history.push(`/inventories`);
    }, [inventory.id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const { organization, user_capabilities: userCapabilities } =
    inventory.summary_fields;

  const deleteDetailsRequests =
    relatedResourceDeleteRequests.inventory(inventory);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={t`Name`}
          value={inventory.name}
          dataCy="constructed-inventory-name"
        />
        <Detail
          label={t`Description`}
          value={inventory.description}
          dataCy="constructed-inventory-description"
        />
        <Detail
          label={t`Type`}
          value={t`Constructed Inventory`}
          dataCy="constructed-inventory-type"
        />
        <Detail
          label={actions.limit.label}
          value={inventory.limit}
          helpText={actions.limit.help_text}
          dataCy="constructed-inventory-limit"
        />
        <Detail
          label={t`Organization`}
          dataCy="constructed-inventory-organization"
          value={
            <Link to={`/organizations/${organization.id}/details`}>
              {organization.name}
            </Link>
          }
        />
        <Detail
          label={actions.total_groups.label}
          value={inventory.total_groups}
          helpText={actions.total_groups.help_text}
          dataCy="constructed-inventory-total-groups"
        />
        <Detail
          label={actions.total_hosts.label}
          value={inventory.total_hosts}
          helpText={actions.total_hosts.help_text}
          dataCy="constructed-inventory-total-hosts"
        />
        <Detail
          label={actions.total_inventory_sources.label}
          value={inventory.total_inventory_sources}
          helpText={actions.total_inventory_sources.help_text}
          dataCy="constructed-inventory-sources"
        />
        <Detail
          label={actions.update_cache_timeout.label}
          value={inventory.update_cache_timeout}
          helpText={actions.update_cache_timeout.help_text}
          dataCy="constructed-inventory-cache-timeout"
        />
        <Detail
          label={actions.inventory_sources_with_failures.label}
          value={inventory.inventory_sources_with_failures}
          helpText={actions.inventory_sources_with_failures.help_text}
          dataCy="constructed-inventory-sources-with-failures"
        />
        <Detail
          label={actions.verbosity.label}
          value={inventory.verbosity}
          helpText={actions.verbosity.help_text}
          dataCy="constructed-inventory-verbosity"
        />
        {instanceGroups && (
          <Detail
            fullWidth
            label={t`Instance Groups`}
            value={<InstanceGroupLabels labels={instanceGroups} isLinkable />}
            isEmpty={instanceGroups.length === 0}
            dataCy="constructed-inventory-instance-groups"
          />
        )}
        {inventory.prevent_instance_group_fallback && (
          <Detail
            fullWidth
            label={t`Enabled Options`}
            dataCy="constructed-inventory-instance-group-fallback"
            value={
              <TextList component={TextListVariants.ul}>
                {inventory.prevent_instance_group_fallback && (
                  <TextListItem component={TextListItemVariants.li}>
                    {t`Prevent Instance Group Fallback`}
                    <Popover
                      header={t`Prevent Instance Group Fallback`}
                      content={helpText.preventInstanceGroupFallback}
                    />
                  </TextListItem>
                )}
              </TextList>
            }
          />
        )}
        <Detail
          fullWidth
          helpText={helpText.labels}
          dataCy="constructed-inventory-labels"
          label={t`Labels`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={inventory.summary_fields.labels?.results?.length}
            >
              {inventory.summary_fields.labels?.results?.map((l) => (
                <Chip key={l.id} isReadOnly>
                  {l.name}
                </Chip>
              ))}
            </ChipGroup>
          }
          isEmpty={inventory.summary_fields.labels?.results?.length === 0}
        />
        <Detail
          fullWidth
          label={t`Source Inventories`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={sourceInventories?.length}
              ouiaId="source-inventory-chips"
            >
              {sourceInventories?.map((sourceInventory) => (
                <Link
                  key={sourceInventory.id}
                  to={`/inventories/inventory/${sourceInventory.id}/details`}
                >
                  <Chip key={sourceInventory.id} isReadOnly>
                    {sourceInventory.name}
                  </Chip>
                </Link>
              ))}
            </ChipGroup>
          }
          isEmpty={sourceInventories?.length === 0}
        />
        <VariablesDetail
          label={actions.source_vars.label}
          helpText={helpText.variables()}
          value={inventory.source_vars}
          rows={4}
          name="variables"
          dataCy="inventory-detail-variables"
        />
        <UserDateDetail
          label={actions.created.label}
          date={inventory.created}
          user={inventory.summary_fields.created_by}
        />
        <UserDateDetail
          label={actions.modified.label}
          date={inventory.modified}
          user={inventory.summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {userCapabilities.edit && (
          <Button
            ouiaId="inventory-detail-edit-button"
            component={Link}
            to={`/inventories/constructed_inventory/${inventory.id}/edit`}
          >
            {t`Edit`}
          </Button>
        )}
        {userCapabilities.delete && (
          <DeleteButton
            name={inventory.name}
            modalTitle={t`Delete Inventory`}
            onConfirm={deleteInventory}
            deleteDetailsRequests={deleteDetailsRequests}
            deleteMessage={t`This inventory is currently being used by other resources. Are you sure you want to delete it?`}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete inventory.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

ConstructedInventoryDetail.propTypes = {
  inventory: Inventory.isRequired,
};

export default ConstructedInventoryDetail;
