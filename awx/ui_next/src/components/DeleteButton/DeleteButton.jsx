import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Button, Badge, Alert, Tooltip } from '@patternfly/react-core';
import AlertModal from '../AlertModal';
import { getRelatedResourceDeleteCounts } from '../../util/getRelatedResourceDeleteDetails';
import ErrorDetail from '../ErrorDetail';

const WarningMessage = styled(Alert)`
  margin-top: 10px;
`;
const Label = styled.span`
  && {
    margin-right: 10px;
  }
`;
function DeleteButton({
  onConfirm,
  modalTitle,
  name,
  i18n,
  variant,
  children,
  isDisabled,
  ouiaId,
  deleteMessage,
  deleteDetailsRequests,
  disabledTooltip,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [deleteMessageError, setDeleteMessageError] = useState();
  const [deleteDetails, setDeleteDetails] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const toggleModal = async isModalOpen => {
    setIsLoading(true);
    if (deleteDetailsRequests?.length && isModalOpen) {
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
    setIsOpen(isModalOpen);
  };

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
      {disabledTooltip ? (
        <Tooltip content={disabledTooltip} position="top">
          <div>
            <Button
              isLoading={isLoading}
              spinnerAriaValueText={isLoading ? 'Loading' : undefined}
              variant={variant || 'secondary'}
              aria-label={i18n._(t`Delete`)}
              isDisabled={isDisabled}
              onClick={() => toggleModal(true)}
              ouiaId={ouiaId}
            >
              {children || i18n._(t`Delete`)}
            </Button>
          </div>
        </Tooltip>
      ) : (
        <Button
          isLoading={isLoading}
          spinnerAriaValueText={isLoading ? 'Loading' : undefined}
          variant={variant || 'secondary'}
          aria-label={i18n._(t`Delete`)}
          isDisabled={isDisabled}
          onClick={() => toggleModal(true)}
        >
          {children || i18n._(t`Delete`)}
        </Button>
      )}
      <AlertModal
        isOpen={isOpen}
        title={modalTitle}
        variant="danger"
        onClose={() => toggleModal(false)}
        actions={[
          <Button
            ouiaId="delete-modal-confirm"
            key="delete"
            variant="danger"
            aria-label={i18n._(t`Confirm Delete`)}
            isDisabled={isDisabled}
            onClick={() => {
              onConfirm();
              toggleModal(false);
            }}
          >
            {i18n._(t`Delete`)}
          </Button>,
          <Button
            ouiaId="delete-modal-cancel"
            key="cancel"
            variant="link"
            aria-label={i18n._(t`Cancel`)}
            onClick={() => toggleModal(false)}
          >
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        {i18n._(t`Are you sure you want to delete:`)}
        <br />
        <strong>{name}</strong>
        {Object.values(deleteDetails).length > 0 && (
          <WarningMessage
            variant="warning"
            isInline
            title={
              <div>
                <div aria-label={deleteMessage}>{deleteMessage}</div>
                <br />
                {Object.entries(deleteDetails).map(([key, value]) => (
                  <div aria-label={`${key}: ${value}`} key={key}>
                    <Label>{key}</Label> <Badge>{value}</Badge>
                  </div>
                ))}
              </div>
            }
          />
        )}
      </AlertModal>
    </>
  );
}

DeleteButton.propTypes = {
  ouiaId: PropTypes.string,
};

DeleteButton.defaultProps = {
  ouiaId: null,
};

export default withI18n()(DeleteButton);
