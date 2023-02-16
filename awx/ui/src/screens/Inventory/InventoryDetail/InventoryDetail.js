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
import { InventoriesAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { Inventory } from 'types';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import InstanceGroupLabels from 'components/InstanceGroupLabels';
import { VERBOSITY } from 'components/VerbositySelectField';
import getHelpText from '../shared/Inventory.helptext';

function InventoryDetail({ inventory }) {
  const history = useHistory();
  const helpText = getHelpText();
  const {
    result: instanceGroups,
    isLoading,
    error: instanceGroupsError,
    request: fetchInstanceGroups,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InventoriesAPI.readInstanceGroups(inventory.id);
      return data.results;
    }, [inventory.id]),
    []
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const { request: deleteInventory, error: deleteError } = useRequest(
    useCallback(async () => {
      await InventoriesAPI.destroy(inventory.id);
      history.push(`/inventories`);
    }, [inventory.id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const { organization, user_capabilities: userCapabilities } =
    inventory.summary_fields;

  const { prevent_instance_group_fallback } = inventory;

  const deleteDetailsRequests =
    relatedResourceDeleteRequests.inventory(inventory);

  const renderOptionsField = prevent_instance_group_fallback;

  const renderOptions = (
    <TextList component={TextListVariants.ul}>
      {prevent_instance_group_fallback && (
        <TextListItem component={TextListItemVariants.li}>
          {t`Prevent Instance Group Fallback`}
        </TextListItem>
      )}
    </TextList>
  );

  if (isLoading) {
    return <ContentLoading />;
  }

  if (instanceGroupsError) {
    return <ContentError error={instanceGroupsError} />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={t`Name`}
          value={inventory.name}
          dataCy="inventory-detail-name"
        />
        <Detail label={t`Description`} value={inventory.description} />
        <Detail label={t`Type`} value={t`Inventory`} />
        <Detail
          label={t`Organization`}
          value={
            <Link to={`/organizations/${organization.id}/details`}>
              {organization.name}
            </Link>
          }
        />
        <Detail label={t`Total hosts`} value={inventory.total_hosts} />
        <Detail label={t`Total groups`} value={inventory.total_groups} />
        {instanceGroups && (
          <Detail
            fullWidth
            label={t`Instance Groups`}
            value={<InstanceGroupLabels labels={instanceGroups} isLinkable />}
            isEmpty={instanceGroups.length === 0}
          />
        )}
        {prevent_instance_group_fallback && (
          <Detail
            label={t`Prevent Instance Group Fallback`}
            dataCy="inv-detail-prevent-instnace-group-fallback"
            helpText={helpText.preventInstanceGroupFallback}
          />
        )}
        <Detail
          label={t`Limit`}
          dataCy="inv-detail-limit"
          value={inventory.limit}
        />
        <Detail
          label={t`Cache timeout`}
          value={inventory.update_cache_timeout}
          dataCy="inv-detail-cache-timeout"
        />
        <Detail
          label={t`Verbosity`}
          dataCy="inv-detail-verbosity"
          value={VERBOSITY()[inventory.verbosity]}
        />
        {renderOptionsField && (
          <Detail
            fullWidth
            label={t`Enabled Options`}
            value={renderOptions}
            dataCy="jt-detail-enabled-options"
            helpText={helpText.enabledOptions}
          />
        )}
        {inventory.summary_fields.labels && (
          <Detail
            fullWidth
            helpText={helpText.labels}
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
        )}
        <VariablesDetail
          label={t`Variables`}
          helpText={helpText.variables()}
          value={inventory.variables || inventory.source_vars}
          rows={4}
          name="variables"
          dataCy="inventory-detail-variables"
        />
        <UserDateDetail
          label={t`Created`}
          date={inventory.created}
          user={inventory.summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={inventory.modified}
          user={inventory.summary_fields.modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {userCapabilities.edit && (
          <Button
            ouiaId="inventory-detail-edit-button"
            component={Link}
            to={`/inventories/inventory/${inventory.id}/edit`}
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
InventoryDetail.propTypes = {
  inventory: Inventory.isRequired,
};

export default InventoryDetail;
