import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { func, bool, arrayOf, object } from 'prop-types';
import AlertModal from '@components/AlertModal';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Radio } from '@patternfly/react-core';
import styled from 'styled-components';

const ListItem = styled.li`
  display: flex;
  font-weight: 600;
  color: var(--pf-global--danger-color--100);
`;

const InventoryGroupsDeleteModal = ({
  onClose,
  onDelete,
  isModalOpen,
  groups,
  i18n,
}) => {
  const [radioOption, setRadioOption] = useState(null);

  return ReactDOM.createPortal(
    <AlertModal
      isOpen={isModalOpen}
      variant="danger"
      title={
        groups.length > 1 ? i18n._(t`Delete Groups?`) : i18n._(t`Delete Group?`)
      }
      onClose={onClose}
      actions={[
        <Button
          aria-label={i18n._(t`Delete`)}
          onClick={() => onDelete(radioOption)}
          variant="danger"
          key="delete"
          isDisabled={radioOption === null}
        >
          {i18n._(t`Delete`)}
        </Button>,
        <Button
          aria-label={i18n._(t`Close`)}
          onClick={onClose}
          variant="secondary"
          key="cancel"
        >
          {i18n._(t`Cancel`)}
        </Button>,
      ]}
    >
      {i18n._(
        t`Are you sure you want to delete the ${
          groups.length > 1 ? i18n._(t`groups`) : i18n._(t`group`)
        } below?`
      )}
      <div css="padding: 24px 0;">
        {groups.map(group => {
          return <ListItem key={group.id}>{group.name}</ListItem>;
        })}
      </div>
      <div>
        <Radio
          id="radio-delete"
          key="radio-delete"
          label={i18n._(t`Delete All Groups and Hosts`)}
          name="option"
          onChange={() => setRadioOption('delete')}
        />
        <Radio
          css="margin-top: 5px;"
          id="radio-promote"
          key="radio-promote"
          label={i18n._(t`Promote Child Groups and Hosts`)}
          name="option"
          onChange={() => setRadioOption('promote')}
        />
      </div>
    </AlertModal>,
    document.body
  );
};

InventoryGroupsDeleteModal.propTypes = {
  onClose: func.isRequired,
  onDelete: func.isRequired,
  isModalOpen: bool,
  groups: arrayOf(object),
};

InventoryGroupsDeleteModal.defaultProps = {
  isModalOpen: false,
  groups: [],
};

export default withI18n()(InventoryGroupsDeleteModal);
