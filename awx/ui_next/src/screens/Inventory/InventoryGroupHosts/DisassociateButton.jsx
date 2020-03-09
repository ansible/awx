import React, { useState } from 'react';
import { arrayOf, func, object, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import styled from 'styled-components';

const ModalNote = styled.div`
  margin-bottom: var(--pf-global--spacer--xl);
`;

function DisassociateButton({
  i18n,
  itemsToDisassociate = [],
  modalNote = '',
  modalTitle = i18n._(t`Disassociate?`),
  onDisassociate,
}) {
  const [isOpen, setIsOpen] = useState(false);

  function handleDisassociate() {
    onDisassociate();
    setIsOpen(false);
  }

  function cannotDisassociate(item) {
    return !item.summary_fields.user_capabilities.delete;
  }

  function renderTooltip() {
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
    if (itemsToDisassociate.length) {
      return i18n._(t`Disassociate`);
    }
    return i18n._(t`Select a row to disassociate`);
  }

  const isDisabled =
    itemsToDisassociate.length === 0 ||
    itemsToDisassociate.some(cannotDisassociate);

  // NOTE: Once PF supports tooltips on disabled elements,
  // we can delete the extra <div> around the <DeleteButton> below.
  // See: https://github.com/patternfly/patternfly-react/issues/1894
  return (
    <>
      <Tooltip content={renderTooltip()} position="top">
        <div>
          <Button
            variant="danger"
            aria-label={i18n._(t`Disassociate`)}
            onClick={() => setIsOpen(true)}
            isDisabled={isDisabled}
          >
            {i18n._(t`Disassociate`)}
          </Button>
        </div>
      </Tooltip>

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
              <strong>{item.name}</strong>
              <br />
            </span>
          ))}
        </AlertModal>
      )}
    </>
  );
}

DisassociateButton.propTypes = {
  itemsToDisassociate: arrayOf(object),
  modalNote: string,
  modalTitle: string,
  onDisassociate: func.isRequired,
};

export default withI18n()(DisassociateButton);
