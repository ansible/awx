import React, { useContext, useEffect, useState } from 'react';
import {
  func,
  bool,
  node,
  number,
  string,
  arrayOf,
  shape,
  checkPropTypes,
} from 'prop-types';
import styled from 'styled-components';
import {
  Alert,
  Badge,
  Button,
  DropdownItem,
  Tooltip,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { KebabifiedContext } from 'contexts/Kebabified';
import { getRelatedResourceDeleteCounts } from 'util/getRelatedResourceDeleteDetails';
import AlertModal from '../AlertModal';

import ErrorDetail from '../ErrorDetail';

const WarningMessage = styled(Alert)`
  margin-top: 10px;
`;

const Label = styled.span`
  && {
    margin-right: 10px;
  }
`;

const requiredField = (props) => {
  const { name, username, image } = props;
  if (!name && !username && !image) {
    return new Error(
      `One of 'name', 'username' or 'image' is required by ItemToDelete component.`
    );
  }
  if (name) {
    checkPropTypes(
      {
        name: string,
      },
      { name: props.name },
      'prop',
      'ItemToDelete'
    );
  }
  if (username) {
    checkPropTypes(
      {
        username: string,
      },
      { username: props.username },
      'prop',
      'ItemToDelete'
    );
  }
  if (image) {
    checkPropTypes(
      {
        image: string,
      },
      { image: props.image },
      'prop',
      'ItemToDelete'
    );
  }
  return null;
};

const ItemToDelete = shape({
  id: number.isRequired,
  name: requiredField,
  username: requiredField,
  image: requiredField,
  summary_fields: shape({
    user_capabilities: shape({
      delete: bool.isRequired,
    }).isRequired,
  }).isRequired,
});

function ToolbarDeleteButton({
  itemsToDelete,
  pluralizedItemName,
  errorMessage,
  onDelete,
  deleteDetailsRequests,
  warningMessage,
  deleteMessage,
  cannotDelete,
}) {
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
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

  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isModalOpen);
    }
  }, [isKebabified, isModalOpen, onKebabModalChange]);

  const renderTooltip = () => {
    const itemsUnableToDelete = itemsToDelete
      .filter(cannotDelete)
      .map((item) => item.name || item.username)
      .join(', ');
    if (itemsToDelete.some(cannotDelete)) {
      return (
        <div>
          {errorMessage ? (
            <>
              <span>{errorMessage}</span>
              <span>{`: ${itemsUnableToDelete}`}</span>
            </>
          ) : (
            t`You do not have permission to delete ${pluralizedItemName}: ${itemsUnableToDelete}`
          )}
        </div>
      );
    }
    if (itemsToDelete.length) {
      return t`Delete`;
    }
    return t`Select a row to delete`;
  };

  const modalTitle = t`Delete ${pluralizedItemName}?`;

  const isDisabled =
    itemsToDelete.length === 0 || itemsToDelete.some(cannotDelete);

  const buildDeleteWarning = () => {
    const deleteMessages = [];
    if (warningMessage) {
      deleteMessages.push(warningMessage);
    }
    if (deleteMessage) {
      if (
        itemsToDelete[0]?.type !== 'inventory' &&
        (itemsToDelete.length > 1 || deleteDetails)
      ) {
        deleteMessages.push(deleteMessage);
      } else if (deleteDetails || itemsToDelete.length > 1) {
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
      {isKebabified ? (
        <Tooltip content={renderTooltip()} position="top">
          <DropdownItem
            key="add"
            isDisabled={isDisabled}
            isLoading={isLoading}
            ouiaId="delete-button"
            spinnerAriaValueText={isLoading ? 'Loading' : undefined}
            component="button"
            onClick={() => {
              toggleModal(true);
            }}
          >
            {t`Delete`}
          </DropdownItem>
        </Tooltip>
      ) : (
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
      )}

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
          <div>{t`This action will delete the following:`}</div>
          {itemsToDelete.map((item) => (
            <span key={item.id} id={`item-to-be-deleted-${item.id}`}>
              <strong>{item.name || item.username || item.image}</strong>
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

ToolbarDeleteButton.propTypes = {
  onDelete: func.isRequired,
  itemsToDelete: arrayOf(ItemToDelete).isRequired,
  pluralizedItemName: string,
  warningMessage: node,
  cannotDelete: func,
};

ToolbarDeleteButton.defaultProps = {
  pluralizedItemName: 'Items',
  warningMessage: null,
  cannotDelete: (item) => !item.summary_fields.user_capabilities.delete,
};

export default ToolbarDeleteButton;
