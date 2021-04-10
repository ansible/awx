import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import {
  Button,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
  Modal,
  Title,
} from '@patternfly/react-core';
import {
  TableComposable,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from '@patternfly/react-table';
import { ExclamationTriangleIcon } from '@patternfly/react-icons';

import { ConfigAPI } from '../../../../api';
import { formatDateStringUTC } from '../../../../util/dates';
import useRequest from '../../../../util/useRequest';
import useSelected from '../../../../util/useSelected';
import ErrorDetail from '../../../../components/ErrorDetail';
import ContentEmpty from '../../../../components/ContentEmpty';
import ContentLoading from '../../../../components/ContentLoading';

function SubscriptionModal({
  i18n,
  subscriptionCreds = {},
  selectedSubscription = null,
  onClose,
  onConfirm,
}) {
  const {
    isLoading,
    error,
    request: fetchSubscriptions,
    result: subscriptions,
  } = useRequest(
    useCallback(async () => {
      if (!subscriptionCreds.username || !subscriptionCreds.password) {
        return [];
      }
      const { data } = await ConfigAPI.readSubscriptions(
        subscriptionCreds.username,
        subscriptionCreds.password
      );
      return data;
    }, []), // eslint-disable-line react-hooks/exhaustive-deps
    []
  );

  const { selected, handleSelect } = useSelected(subscriptions);

  function handleConfirm() {
    const [subscription] = selected;
    onConfirm(subscription);
    onClose();
  }

  useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  useEffect(() => {
    if (selectedSubscription?.pool_id) {
      handleSelect({ pool_id: selectedSubscription.pool_id });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Modal
      aria-label={i18n._(t`Subscription selection modal`)}
      isOpen
      onClose={onClose}
      title={i18n._(t`Select a subscription`)}
      width="50%"
      actions={[
        <Button
          aria-label={i18n._(t`Confirm selection`)}
          isDisabled={selected.length === 0}
          key="confirm"
          onClick={handleConfirm}
          variant="primary"
          ouiaId="subscription-modal-confirm"
        >
          <Trans>Select</Trans>
        </Button>,
        <Button
          aria-label={i18n._(t`Cancel`)}
          key="cancel"
          onClick={onClose}
          variant="link"
          ouiaId="subscription-modal-cancel"
        >
          <Trans>Cancel</Trans>
        </Button>,
      ]}
    >
      {isLoading && <ContentLoading />}
      {!isLoading && error && (
        <>
          <EmptyState variant="full">
            <EmptyStateIcon icon={ExclamationTriangleIcon} />
            <Title size="lg" headingLevel="h3">
              <Trans>No subscriptions found</Trans>
            </Title>
            <EmptyStateBody>
              <Trans>
                We were unable to locate licenses associated with this account.
              </Trans>{' '}
              <Button
                aria-label={i18n._(t`Close subscription modal`)}
                onClick={onClose}
                variant="link"
                isInline
                ouiaId="subscription-modal-close"
              >
                <Trans>Return to subscription management.</Trans>
              </Button>
            </EmptyStateBody>
            <ErrorDetail error={error} />
          </EmptyState>
        </>
      )}
      {!isLoading && !error && subscriptions?.length === 0 && (
        <ContentEmpty
          title={i18n._(t`No subscriptions found`)}
          message={i18n._(
            t`We were unable to locate subscriptions associated with this account.`
          )}
        />
      )}
      {!isLoading && !error && subscriptions?.length > 0 && (
        <TableComposable
          variant="compact"
          aria-label={i18n._(t`Subscriptions table`)}
        >
          <Thead>
            <Tr>
              <Th />
              <Th>{i18n._(t`Name`)}</Th>
              <Th modifier="fitContent">{i18n._(t`Managed nodes`)}</Th>
              <Th modifier="fitContent">{i18n._(t`Expires`)}</Th>
            </Tr>
          </Thead>
          <Tbody>
            {subscriptions.map(subscription => (
              <Tr key={`row-${subscription.pool_id}`} id={subscription.pool_id}>
                <Td
                  key={`row-${subscription.pool_id}`}
                  select={{
                    onSelect: () => handleSelect(subscription),
                    isSelected: selected.some(
                      row => row.pool_id === subscription.pool_id
                    ),
                    variant: 'radio',
                    rowIndex: `row-${subscription.pool_id}`,
                  }}
                />
                <Td dataLabel={i18n._(t`Trial`)}>
                  {subscription.subscription_name}
                </Td>
                <Td dataLabel={i18n._(t`Managed nodes`)}>
                  {subscription.instance_count}
                </Td>
                <Td dataLabel={i18n._(t`Expires`)} modifier="nowrap">
                  {formatDateStringUTC(
                    new Date(subscription.license_date * 1000).toISOString()
                  )}
                </Td>
              </Tr>
            ))}
          </Tbody>
        </TableComposable>
      )}
    </Modal>
  );
}

export default withI18n()(SubscriptionModal);
