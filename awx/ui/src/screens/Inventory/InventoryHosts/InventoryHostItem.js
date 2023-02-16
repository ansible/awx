import React, { useCallback } from 'react';
import { string, bool, func } from 'prop-types';
import { t } from '@lingui/macro';
import { Tr, Td } from '@patternfly/react-table';
import { Link, useParams } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import { Button, Chip } from '@patternfly/react-core';
import { HostsAPI } from 'api';
import AlertModal from 'components/AlertModal';
import ChipGroup from 'components/ChipGroup';
import ErrorDetail from 'components/ErrorDetail';
import HostToggle from 'components/HostToggle';
import { ActionsTd, ActionItem, TdBreakWord } from 'components/PaginatedTable';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { Host } from 'types';

function InventoryHostItem({
  detailUrl,
  editUrl,
  host,
  isSelected,
  onSelect,
  rowIndex,
}) {
  const { inventoryType } = useParams();

  const labelId = `check-action-${host.id}`;
  const initialGroups = host?.summary_fields?.groups ?? {
    results: [],
    count: 0,
  };

  const {
    error,
    request: fetchRelatedGroups,
    result: relatedGroups,
  } = useRequest(
    useCallback(async (hostId) => {
      const { data } = await HostsAPI.readGroups(hostId);
      return data.results;
    }, []),
    initialGroups.results
  );

  const { error: dismissableError, dismissError } = useDismissableError(error);

  const handleOverflowChipClick = (hostId) => {
    if (relatedGroups.length === initialGroups.count) {
      return;
    }
    fetchRelatedGroups(hostId);
  };

  return (
    <>
      <Tr id={`host-row-${host.id}`} ouiaId={`inventory-host-row-${host.id}`}>
        <Td
          data-cy={labelId}
          select={{
            rowIndex,
            isSelected,
            onSelect,
          }}
        />
        <TdBreakWord id={labelId} dataLabel={t`Name`}>
          <Link to={`${detailUrl}`}>
            <b>{host.name}</b>
          </Link>
        </TdBreakWord>
        <TdBreakWord
          id={`host-description-${host.id}`}
          dataLabel={t`Description`}
        >
          {host.description}
        </TdBreakWord>
        <TdBreakWord
          id={`host-related-groups-${host.id}`}
          dataLabel={t`Related Groups`}
        >
          <ChipGroup
            aria-label={t`Related Groups`}
            numChips={4}
            totalChips={initialGroups.count}
            ouiaId="host-related-groups-chips"
            onOverflowChipClick={() => handleOverflowChipClick(host.id)}
          >
            {relatedGroups.map((group) => (
              <Chip key={group.name} isReadOnly>
                {group.name}
              </Chip>
            ))}
          </ChipGroup>
        </TdBreakWord>
        <ActionsTd
          aria-label={t`Actions`}
          dataLabel={t`Actions`}
          gridColumns="auto 40px"
        >
          <HostToggle host={host} />
          {inventoryType !== 'constructed_inventory' && (
            <ActionItem
              visible={host.summary_fields.user_capabilities?.edit}
              tooltip={t`Edit host`}
            >
              <Button
                aria-label={t`Edit host`}
                ouiaId={`${host.id}-edit-button`}
                variant="plain"
                component={Link}
                to={`${editUrl}`}
              >
                <PencilAltIcon />
              </Button>
            </ActionItem>
          )}
        </ActionsTd>
      </Tr>
      {dismissableError && (
        <AlertModal
          isOpen={dismissableError}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {t`Failed to load related groups.`}
          <ErrorDetail error={dismissableError} />
        </AlertModal>
      )}
    </>
  );
}

InventoryHostItem.propTypes = {
  detailUrl: string.isRequired,
  host: Host.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default InventoryHostItem;
