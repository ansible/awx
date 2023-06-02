import React, { useState, useEffect, useContext } from 'react';
import {
  arrayOf,
  func,
  shape,
  string,
  oneOfType,
  number,
  node,
} from 'prop-types';

import { t } from '@lingui/macro';
import { Button, Tooltip, DropdownItem } from '@patternfly/react-core';
import styled from 'styled-components';
import { KebabifiedContext } from 'contexts/Kebabified';

import AlertModal from '../AlertModal';

const ModalNote = styled.div`
  margin-bottom: var(--pf-global--spacer--xl);
`;

function DisassociateButton({
  itemsToDisassociate = [],
  modalNote = '',
  modalTitle = t`Disassociate?`,
  onDisassociate,
  verifyCannotDisassociate = true,
  isProtectedInstanceGroup = false,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);

  const handleDisassociate = () => {
    onDisassociate();
    setIsOpen(false);
  };

  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isOpen);
    }
  }, [isKebabified, isOpen, onKebabModalChange]);

  function cannotDisassociateAllOthers(item) {
    return !item.summary_fields?.user_capabilities?.delete;
  }
  function cannotDisassociateInstances(item) {
    return (
      item.node_type === 'control' ||
      (isProtectedInstanceGroup && item.node_type === 'hybrid')
    );
  }

  const cannotDisassociate = itemsToDisassociate.some(
    (i) => i.type === 'instance'
  )
    ? cannotDisassociateInstances
    : cannotDisassociateAllOthers;

  function renderTooltip() {
    if (verifyCannotDisassociate) {
      const itemsUnableToDisassociate = itemsToDisassociate
        .filter(cannotDisassociate)
        .map((item) => item.name ?? item.hostname)
        .join(', ');
      if (
        cannotDisassociate
          ? itemsToDisassociate.some(cannotDisassociateInstances)
          : itemsToDisassociate.some(cannotDisassociateAllOthers)
      ) {
        return (
          <div>
            {t`You do not have permission to disassociate the following: ${itemsUnableToDisassociate}`}
          </div>
        );
      }
    }

    if (itemsToDisassociate.length) {
      return t`Disassociate`;
    }
    return t`Select a row to disassociate`;
  }

  let isDisabled = false;
  if (verifyCannotDisassociate) {
    isDisabled = itemsToDisassociate.some(cannotDisassociate);
  }

  // NOTE: Once PF supports tooltips on disabled elements,
  // we can delete the extra <div> around the <DeleteButton> below.
  // See: https://github.com/patternfly/patternfly-react/issues/1894
  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="add"
          aria-label={t`disassociate`}
          isDisabled={isDisabled || !itemsToDisassociate.length}
          component="button"
          ouiaId="disassociate-tooltip"
          onClick={() => setIsOpen(true)}
        >
          {t`Disassociate`}
        </DropdownItem>
      ) : (
        <Tooltip
          content={renderTooltip()}
          ouiaId="disassociate-tooltip"
          position="top"
        >
          <div>
            <Button
              ouiaId="disassociate-button"
              variant="secondary"
              aria-label={t`Disassociate`}
              onClick={() => setIsOpen(true)}
              isDisabled={isDisabled || !itemsToDisassociate.length}
            >
              {t`Disassociate`}
            </Button>
          </div>
        </Tooltip>
      )}

      {isOpen && (
        <AlertModal
          isOpen={isOpen}
          title={modalTitle}
          variant="warning"
          onClose={() => setIsOpen(false)}
          actions={[
            <Button
              ouiaId="disassociate-modal-confirm"
              key="disassociate"
              variant="danger"
              aria-label={t`confirm disassociate`}
              onClick={handleDisassociate}
            >
              {t`Disassociate`}
            </Button>,
            <Button
              ouiaId="disassociate-modal-cancel"
              key="cancel"
              variant="link"
              aria-label={t`Cancel`}
              onClick={() => setIsOpen(false)}
            >
              {t`Cancel`}
            </Button>,
          ]}
        >
          {modalNote && <ModalNote>{modalNote}</ModalNote>}

          <div>{t`This action will disassociate the following:`}</div>

          {itemsToDisassociate.map((item) => (
            <span key={item.id}>
              <strong>{item.hostname ? item.hostname : item.name}</strong>
              <br />
            </span>
          ))}
        </AlertModal>
      )}
    </>
  );
}

DisassociateButton.defaultProps = {
  itemsToDisassociate: [],
  modalNote: '',
  modalTitle: '',
};

DisassociateButton.propTypes = {
  itemsToDisassociate: oneOfType([
    arrayOf(
      shape({
        id: number.isRequired,
        name: string.isRequired,
      })
    ),
    arrayOf(
      shape({
        id: number.isRequired,
        hostname: string.isRequired,
      })
    ),
  ]),
  modalNote: node,
  modalTitle: string,
  onDisassociate: func.isRequired,
};

export default DisassociateButton;
