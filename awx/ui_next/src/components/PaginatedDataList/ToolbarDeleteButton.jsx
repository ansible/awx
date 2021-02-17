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
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '../AlertModal';
import { KebabifiedContext } from '../../contexts/Kebabified';
import { getRelatedResourceDeleteCounts } from '../../util/getRelatedResourceDeleteDetails';

import ErrorDetail from '../ErrorDetail';

const WarningMessage = styled(Alert)`
  margin-top: 10px;
`;
const DetailsWrapper = styled.span`
  :not(:first-of-type) {
    padding-left: 10px;
  }
`;

const requiredField = props => {
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
  i18n,
  cannotDelete,
}) {
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteDetails, setDeleteDetails] = useState({});

  const deleteMessages = [warningMessage, deleteMessage].filter(
    message => message
  );

  const [deleteMessageError, setDeleteMessageError] = useState();
  const handleDelete = () => {
    onDelete();
    toggleModal();
  };

  const toggleModal = async isOpen => {
    if (itemsToDelete.length === 1 && deleteDetailsRequests?.length > 0) {
      const { results, error } = await getRelatedResourceDeleteCounts(
        deleteDetailsRequests
      );

      if (error) {
        setDeleteMessageError(error);
      } else {
        setDeleteDetails(results);
      }
    }

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
      .map(item => item.name || item.username)
      .join(', ');
    if (itemsToDelete.some(cannotDelete)) {
      return (
        <div>
          {errorMessage.length > 0
            ? `${errorMessage}: ${itemsUnableToDelete}`
            : i18n._(
                t`You do not have permission to delete ${pluralizedItemName}: ${itemsUnableToDelete}`
              )}
        </div>
      );
    }
    if (itemsToDelete.length) {
      return i18n._(t`Delete`);
    }
    return i18n._(t`Select a row to delete`);
  };

  const modalTitle = i18n._(t`Delete ${pluralizedItemName}?`);

  const isDisabled =
    itemsToDelete.length === 0 || itemsToDelete.some(cannotDelete);

  if (deleteMessageError) {
    return (
      <AlertModal
        isOpen={deleteMessageError}
        title={i18n._(t`Error!`)}
        onClose={() => {
          toggleModal(false);
          setDeleteMessageError();
        }}
      >
        <ErrorDetail error={deleteMessageError} />
      </AlertModal>
    );
  }

  return (
    <>
      {isKebabified ? (
        <Tooltip content={renderTooltip()} position="top">
          <DropdownItem
            key="add"
            isDisabled={isDisabled}
            component="button"
            onClick={() => toggleModal(true)}
          >
            {i18n._(t`Delete`)}
          </DropdownItem>
        </Tooltip>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              variant="secondary"
              aria-label={i18n._(t`Delete`)}
              onClick={() => toggleModal(true)}
              isAriaDisabled={isDisabled}
            >
              {i18n._(t`Delete`)}
            </Button>
          </div>
        </Tooltip>
      )}

      {isModalOpen && !deleteMessageError && (
        <AlertModal
          variant="danger"
          title={modalTitle}
          isOpen={isModalOpen}
          onClose={() => toggleModal(false)}
          actions={[
            <Button
              key="delete"
              variant="danger"
              aria-label={i18n._(t`confirm delete`)}
              onClick={handleDelete}
            >
              {i18n._(t`Delete`)}
            </Button>,
            <Button
              key="cancel"
              variant="link"
              aria-label={i18n._(t`cancel delete`)}
              onClick={() => toggleModal(false)}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          <div>{i18n._(t`This action will delete the following:`)}</div>
          {itemsToDelete.map(item => (
            <span key={item.id}>
              <strong>{item.name || item.username || item.image}</strong>
              <br />
            </span>
          ))}
          {itemsToDelete.length === 1 &&
            Object.values(deleteDetails).length > 0 && (
              <WarningMessage
                variant="warning"
                isInline
                title={
                  <div>
                    {deleteMessages.map(message => (
                      <div aria-label={message} key={message}>
                        {message}
                      </div>
                    ))}
                    {itemsToDelete.length === 1 && (
                      <>
                        <br />
                        {Object.entries(deleteDetails).map(([key, value]) => (
                          <DetailsWrapper
                            key={key}
                            aria-label={`${key}: ${value}`}
                          >
                            <span>{key}</span> <Badge>{value}</Badge>
                          </DetailsWrapper>
                        ))}
                      </>
                    )}
                  </div>
                }
              />
            )}
          {itemsToDelete.length > 1 && (
            <WarningMessage
              variant="warning"
              isInline
              title={deleteMessages.map(message => (
                <div>{message}</div>
              ))}
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
  errorMessage: string,
  warningMessage: node,
  cannotDelete: func,
};

ToolbarDeleteButton.defaultProps = {
  pluralizedItemName: 'Items',
  errorMessage: '',
  warningMessage: null,
  cannotDelete: item => !item.summary_fields.user_capabilities.delete,
};

export default withI18n()(ToolbarDeleteButton);
