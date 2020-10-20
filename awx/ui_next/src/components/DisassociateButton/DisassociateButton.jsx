import React, { useState, useEffect, useContext } from 'react';
import { arrayOf, func, object, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Tooltip, DropdownItem } from '@patternfly/react-core';
import styled from 'styled-components';
import { KebabifiedContext } from '../../contexts/Kebabified';

import AlertModal from '../AlertModal';

const ModalNote = styled.div`
  margin-bottom: var(--pf-global--spacer--xl);
`;

function DisassociateButton({
  i18n,
  itemsToDisassociate = [],
  modalNote = '',
  modalTitle = i18n._(t`Disassociate?`),
  onDisassociate,
  verifyCannotDisassociate = true,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);

  function handleDisassociate() {
    onDisassociate();
    setIsOpen(false);
  }

  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isOpen);
    }
  }, [isKebabified, isOpen, onKebabModalChange]);

  function cannotDisassociate(item) {
    return !item.summary_fields?.user_capabilities?.delete;
  }

  function renderTooltip() {
    if (verifyCannotDisassociate) {
      const itemsUnableToDisassociate = itemsToDisassociate
        .filter(cannotDisassociate)
        .map(item => item.name)
        .join(', ');

      if (itemsToDisassociate.some(cannotDisassociate)) {
        return (
          <div>
            {i18n._(
              t`You do not have permission to disassociate the following: ${itemsUnableToDisassociate}`
            )}
          </div>
        );
      }
    }

    if (itemsToDisassociate.length) {
      return i18n._(t`Disassociate`);
    }
    return i18n._(t`Select a row to disassociate`);
  }

  let isDisabled = false;
  if (verifyCannotDisassociate) {
    isDisabled =
      itemsToDisassociate.length === 0 ||
      itemsToDisassociate.some(cannotDisassociate);
  } else {
    isDisabled = itemsToDisassociate.length === 0;
  }

  // NOTE: Once PF supports tooltips on disabled elements,
  // we can delete the extra <div> around the <DeleteButton> below.
  // See: https://github.com/patternfly/patternfly-react/issues/1894
  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="add"
          aria-label={i18n._(t`disassociate`)}
          isDisabled={isDisabled}
          component="button"
          onClick={() => setIsOpen(true)}
        >
          {i18n._(t`Disassociate`)}
        </DropdownItem>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              variant="secondary"
              aria-label={i18n._(t`Disassociate`)}
              onClick={() => setIsOpen(true)}
              isDisabled={isDisabled}
            >
              {i18n._(t`Disassociate`)}
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
              key="disassociate"
              variant="danger"
              aria-label={i18n._(t`confirm disassociate`)}
              onClick={handleDisassociate}
            >
              {i18n._(t`Disassociate`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`Cancel`)}
              onClick={() => setIsOpen(false)}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          {modalNote && <ModalNote>{modalNote}</ModalNote>}

          <div>{i18n._(t`This action will disassociate the following:`)}</div>

          {itemsToDisassociate.map(item => (
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
  itemsToDisassociate: arrayOf(object),
  modalNote: string,
  modalTitle: string,
  onDisassociate: func.isRequired,
};

export default withI18n()(DisassociateButton);
