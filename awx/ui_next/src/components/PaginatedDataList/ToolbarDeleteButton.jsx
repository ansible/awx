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
import { Alert, Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '../AlertModal';
import { KebabifiedContext } from '../../contexts/Kebabified';

const WarningMessage = styled(Alert)`
  margin-top: 10px;
`;

const requireNameOrUsername = props => {
  const { name, username } = props;
  if (!name && !username) {
    return new Error(
      `One of 'name' or 'username' is required by ItemToDelete component.`
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
  return null;
};

const ItemToDelete = shape({
  id: number.isRequired,
  name: requireNameOrUsername,
  username: requireNameOrUsername,
  summary_fields: shape({
    user_capabilities: shape({
      delete: bool.isRequired,
    }).isRequired,
  }).isRequired,
});

function cannotDelete(item) {
  return !item.summary_fields.user_capabilities.delete;
}

function ToolbarDeleteButton({
  itemsToDelete,
  pluralizedItemName,
  errorMessage,
  onDelete,
  warningMessage,
  i18n,
}) {
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleDelete = () => {
    onDelete();
    toggleModal();
  };

  const toggleModal = () => {
    setIsModalOpen(!isModalOpen);
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
            ? errorMessage
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

  // NOTE: Once PF supports tooltips on disabled elements,
  // we can delete the extra <div> around the <DeleteButton> below.
  // See: https://github.com/patternfly/patternfly-react/issues/1894
  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="add"
          isDisabled={isDisabled}
          component="button"
          onClick={toggleModal}
        >
          {i18n._(t`Delete`)}
        </DropdownItem>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              variant="secondary"
              aria-label={i18n._(t`Delete`)}
              onClick={toggleModal}
              isDisabled={isDisabled}
            >
              {i18n._(t`Delete`)}
            </Button>
          </div>
        </Tooltip>
      )}
      {isModalOpen && (
        <AlertModal
          variant="danger"
          title={modalTitle}
          isOpen={isModalOpen}
          onClose={toggleModal}
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
              variant="secondary"
              aria-label={i18n._(t`cancel delete`)}
              onClick={toggleModal}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          <div>{i18n._(t`This action will delete the following:`)}</div>
          {itemsToDelete.map(item => (
            <span key={item.id}>
              <strong>{item.name || item.username}</strong>
              <br />
            </span>
          ))}
          {warningMessage && (
            <WarningMessage variant="warning" isInline title={warningMessage} />
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
};

ToolbarDeleteButton.defaultProps = {
  pluralizedItemName: 'Items',
  errorMessage: '',
  warningMessage: null,
};

export default withI18n()(ToolbarDeleteButton);
