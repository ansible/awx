import React, { useState } from 'react';
import { func, node, string, arrayOf, shape } from 'prop-types';
import styled from 'styled-components';
import { Alert, Badge, Button, Tooltip } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { getRelatedResourceDeleteCounts } from 'util/getRelatedResourceDeleteDetails';
import AlertModal from '../../components/AlertModal';

import ErrorDetail from '../../components/ErrorDetail';

const WarningMessage = styled(Alert)`
  margin-top: 10px;
`;

const Label = styled.span`
  && {
    margin-right: 10px;
  }
`;

const ItemToDelete = shape({
  hostname: string.isRequired,
});

function HostMetricsDeleteButton({
  itemsToDelete,
  pluralizedItemName,
  onDelete,
  deleteDetailsRequests,
  warningMessage,
  deleteMessage,
}) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteDetails, setDeleteDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [deleteMessageError, setDeleteMessageError] = useState();
  const handleDelete = () => {
    onDelete();
    toggleModal();
  };

  const toggleModal = async (isOpen) => {
    setIsLoading(true);
    setDeleteDetails(null);
    if (
      isOpen &&
      itemsToDelete.length === 1 &&
      deleteDetailsRequests?.length > 0
    ) {
      const { results, error } = await getRelatedResourceDeleteCounts(
        deleteDetailsRequests
      );

      if (error) {
        setDeleteMessageError(error);
      } else {
        setDeleteDetails(results);
      }
    }
    setIsLoading(false);
    setIsModalOpen(isOpen);
  };

  const renderTooltip = () => {
    if (itemsToDelete.length) {
      return t`Soft delete`;
    }
    return t`Select a row to delete`;
  };

  const modalTitle = t`Soft delete ${pluralizedItemName}?`;

  const isDisabled = itemsToDelete.length === 0;

  const buildDeleteWarning = () => {
    const deleteMessages = [];
    if (warningMessage) {
      deleteMessages.push(warningMessage);
    }
    if (deleteMessage) {
      if (itemsToDelete.length > 1 || deleteDetails) {
        deleteMessages.push(deleteMessage);
      }
    }
    return (
      <div>
        {deleteMessages.map((message) => (
          <div aria-label={message} key={message}>
            {message}
          </div>
        ))}
        {deleteDetails &&
          Object.entries(deleteDetails).map(([key, value]) => (
            <div key={key} aria-label={`${key}: ${value}`}>
              <Label>{key}</Label>
              <Badge>{value}</Badge>
            </div>
          ))}
      </div>
    );
  };

  if (deleteMessageError) {
    return (
      <AlertModal
        isOpen={deleteMessageError}
        title={t`Error!`}
        onClose={() => {
          toggleModal(false);
          setDeleteMessageError();
        }}
      >
        <ErrorDetail error={deleteMessageError} />
      </AlertModal>
    );
  }
  const shouldShowDeleteWarning =
    warningMessage ||
    (itemsToDelete.length === 1 && deleteDetails) ||
    (itemsToDelete.length > 1 && deleteMessage);

  return (
    <>
      <Tooltip content={renderTooltip()} position="top">
        <div>
          <Button
            variant="secondary"
            isLoading={isLoading}
            ouiaId="delete-button"
            spinnerAriaValueText={isLoading ? 'Loading' : undefined}
            aria-label={t`Delete`}
            onClick={() => toggleModal(true)}
            isDisabled={isDisabled}
          >
            {t`Delete`}
          </Button>
        </div>
      </Tooltip>
      {isModalOpen && (
        <AlertModal
          variant="danger"
          title={modalTitle}
          isOpen={isModalOpen}
          onClose={() => toggleModal(false)}
          actions={[
            <Button
              ouiaId="delete-modal-confirm"
              key="delete"
              variant="danger"
              aria-label={t`confirm delete`}
              isDisabled={Boolean(
                deleteDetails && itemsToDelete[0]?.type === 'credential_type'
              )}
              onClick={handleDelete}
            >
              {t`Delete`}
            </Button>,
            <Button
              ouiaId="delete-cancel"
              key="cancel"
              variant="link"
              aria-label={t`cancel delete`}
              onClick={() => toggleModal(false)}
            >
              {t`Cancel`}
            </Button>,
          ]}
        >
          <div>{t`This action will soft delete the following:`}</div>
          {itemsToDelete.map((item) => (
            <span
              key={item.hostname}
              id={`item-to-be-deleted-${item.hostname}`}
            >
              <strong>{item.hostname}</strong>
              <br />
            </span>
          ))}
          {shouldShowDeleteWarning && (
            <WarningMessage
              variant="warning"
              isInline
              title={buildDeleteWarning()}
            />
          )}
        </AlertModal>
      )}
    </>
  );
}

HostMetricsDeleteButton.propTypes = {
  onDelete: func.isRequired,
  itemsToDelete: arrayOf(ItemToDelete).isRequired,
  pluralizedItemName: string,
  warningMessage: node,
};

HostMetricsDeleteButton.defaultProps = {
  pluralizedItemName: 'Items',
  warningMessage: null,
};

export default HostMetricsDeleteButton;
