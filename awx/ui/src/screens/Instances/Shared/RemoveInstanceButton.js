import React, { useContext, useState, useEffect } from 'react';
import { t, Plural } from '@lingui/macro';
import { KebabifiedContext } from 'contexts/Kebabified';
import {
  getRelatedResourceDeleteCounts,
  relatedResourceDeleteRequests,
} from 'util/getRelatedResourceDeleteDetails';
import {
  Button,
  DropdownItem,
  Tooltip,
  Alert,
  Badge,
} from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';
import styled from 'styled-components';
import ErrorDetail from 'components/ErrorDetail';

const WarningMessage = styled(Alert)`
  margin-top: 10px;
`;

const Label = styled.span`
  && {
    margin-right: 10px;
  }
`;

function RemoveInstanceButton({ itemsToRemove, onRemove, isK8s }) {
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
  const [removeMessageError, setRemoveMessageError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [removeDetails, setRemoveDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const cannotRemove = (item) => item.node_type !== 'execution';

  const toggleModal = async (isOpen) => {
    setRemoveDetails(null);
    setIsLoading(true);
    if (isOpen && itemsToRemove.length > 0) {
      const { results, error } = await getRelatedResourceDeleteCounts(
        relatedResourceDeleteRequests.instance(itemsToRemove[0])
      );

      if (error) {
        setRemoveMessageError(error);
      } else {
        setRemoveDetails(results);
      }
    }
    setIsModalOpen(isOpen);
    setIsLoading(false);
  };

  const handleRemove = async () => {
    await onRemove();
    toggleModal(false);
  };
  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isModalOpen);
    }
  }, [isKebabified, isModalOpen, onKebabModalChange]);

  const renderTooltip = () => {
    const itemsUnableToremove = itemsToRemove
      .filter(cannotRemove)
      .map((item) => item.hostname)
      .join(', ');
    if (itemsToRemove.some(cannotRemove)) {
      return t`You do not have permission to remove instances: ${itemsUnableToremove}`;
    }
    if (itemsToRemove.length) {
      return t`Remove`;
    }
    return t`Select a row to remove`;
  };

  const isDisabled =
    itemsToRemove.length === 0 || itemsToRemove.some(cannotRemove);

  const buildRemoveWarning = () => (
    <div>
      <Plural
        value={itemsToRemove.length}
        one="This intance is currently being used by other resources. Are you sure you want to delete it?"
        other="Deprovisioning these instances could impact other resources that rely on them. Are you sure you want to delete anyway?"
      />
      {removeDetails &&
        Object.entries(removeDetails).map(([key, value]) => (
          <div key={key} aria-label={`${key}: ${value}`}>
            <Label>{key}</Label>
            <Badge>{value}</Badge>
          </div>
        ))}
    </div>
  );

  if (removeMessageError) {
    return (
      <AlertModal
        isOpen={removeMessageError}
        title={t`Error!`}
        onClose={() => {
          toggleModal(false);
          setRemoveMessageError();
        }}
      >
        <ErrorDetail error={removeMessageError} />
      </AlertModal>
    );
  }
  return (
    <>
      {isKebabified ? (
        <Tooltip content={renderTooltip()} position="top">
          <DropdownItem
            key="add"
            isDisabled={isDisabled || !isK8s}
            isLoading={isLoading}
            ouiaId="remove-button"
            spinnerAriaValueText={isLoading ? 'Loading' : undefined}
            component="button"
            onClick={() => {
              toggleModal(true);
            }}
          >
            {t`Remove`}
          </DropdownItem>
        </Tooltip>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              variant="secondary"
              isLoading={isLoading}
              ouiaId="remove-button"
              spinnerAriaValueText={isLoading ? 'Loading' : undefined}
              onClick={() => toggleModal(true)}
              isDisabled={isDisabled || !isK8s}
            >
              {t`Remove`}
            </Button>
          </div>
        </Tooltip>
      )}

      {isModalOpen && (
        <AlertModal
          variant="danger"
          title={t`Remove Instances`}
          isOpen={isModalOpen}
          onClose={() => toggleModal(false)}
          actions={[
            <Button
              ouiaId="remove-modal-confirm"
              key="remove"
              variant="danger"
              aria-label={t`Confirm remove`}
              onClick={handleRemove}
            >
              {t`Remove`}
            </Button>,
            <Button
              ouiaId="remove-cancel"
              key="cancel"
              variant="link"
              aria-label={t`cancel remove`}
              onClick={() => {
                toggleModal(false);
              }}
            >
              {t`Cancel`}
            </Button>,
          ]}
        >
          <div>{t`This action will remove the following instances:`}</div>
          {itemsToRemove.map((item) => (
            <span key={item.id} id={`item-to-be-removed-${item.id}`}>
              <strong>{item.hostname}</strong>
              <br />
            </span>
          ))}
          {removeDetails && (
            <WarningMessage
              variant="warning"
              isInline
              title={buildRemoveWarning()}
            />
          )}
        </AlertModal>
      )}
    </>
  );
}

export default RemoveInstanceButton;
