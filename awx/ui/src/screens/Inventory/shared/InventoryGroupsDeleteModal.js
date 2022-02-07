import 'styled-components/macro';
import React, { useState, useContext, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { func, bool, arrayOf } from 'prop-types';
import { t, Plural } from '@lingui/macro';
import { Button, Radio, DropdownItem } from '@patternfly/react-core';
import styled from 'styled-components';
import { KebabifiedContext } from 'contexts/Kebabified';
import { GroupsAPI, InventoriesAPI } from 'api';
import { Group } from 'types';
import ErrorDetail from 'components/ErrorDetail';
import AlertModal from 'components/AlertModal';

const ListItem = styled.li`
  display: flex;
  font-weight: 600;
  color: var(--pf-global--danger-color--100);
`;

const InventoryGroupsDeleteModal = ({ onAfterDelete, isDisabled, groups }) => {
  const [radioOption, setRadioOption] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteLoading, setIsDeleteLoading] = useState(false);
  const [deletionError, setDeletionError] = useState(null);
  const { id: inventoryId } = useParams();
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);

  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isModalOpen);
    }
  }, [isKebabified, isModalOpen, onKebabModalChange]);
  const handleDelete = async (option) => {
    setIsDeleteLoading(true);

    try {
      /* eslint-disable no-await-in-loop */
      /* Delete groups sequentially to avoid api integrity errors */
      /* https://eslint.org/docs/rules/no-await-in-loop#when-not-to-use-it */
      for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        if (option === 'delete') {
          await GroupsAPI.destroy(+group.id);
        } else if (option === 'promote') {
          await InventoriesAPI.promoteGroup(inventoryId, +group.id);
        }
      }
      /* eslint-enable no-await-in-loop */
    } catch (error) {
      setDeletionError(error);
    } finally {
      setIsModalOpen(false);
      setIsDeleteLoading(false);
      onAfterDelete();
    }
  };
  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="delete"
          isDisabled={isDisabled || isDeleteLoading}
          component="button"
          aria-label={t`Delete`}
          onClick={() => setIsModalOpen(true)}
          ouiaId="group-delete-dropdown-item"
        >
          {t`Delete`}
        </DropdownItem>
      ) : (
        <Button
          variant="secondary"
          aria-label={t`Delete`}
          onClick={() => setIsModalOpen(true)}
          isDisabled={isDisabled || isDeleteLoading}
          ouiaId="group-delete-button"
        >
          {t`Delete`}
        </Button>
      )}
      {isModalOpen && (
        <AlertModal
          isOpen={isModalOpen}
          variant="danger"
          title={
            <Plural
              value={groups.length}
              one="Delete Group?"
              other="Delete Groups?"
            />
          }
          onClose={() => setIsModalOpen(false)}
          actions={[
            <Button
              aria-label={t`Confirm Delete`}
              onClick={() => handleDelete(radioOption)}
              variant="danger"
              key="delete"
              isDisabled={radioOption === null}
              ouiaId="delete-modal-confirm-button"
            >
              {t`Delete`}
            </Button>,
            <Button
              aria-label={t`Close`}
              onClick={() => setIsModalOpen(false)}
              variant="link"
              key="cancel"
              ouiaId="delete-modal-cancel-button"
            >
              {t`Cancel`}
            </Button>,
          ]}
        >
          <Plural
            value={groups.length}
            one="Are you sure you want delete the group below?"
            other="Are you sure you want delete the groups below?"
          />

          <div css="padding: 24px 0;">
            {groups.map((group) => (
              <ListItem key={group.id}>{group.name}</ListItem>
            ))}
          </div>
          <div>
            <Radio
              id="radio-delete"
              key="radio-delete"
              label={t`Delete All Groups and Hosts`}
              name="option"
              onChange={() => setRadioOption('delete')}
              ouiaId="delete-all-radio-button"
            />
            <Radio
              css="margin-top: 5px;"
              id="radio-promote"
              key="radio-promote"
              label={t`Promote Child Groups and Hosts`}
              name="option"
              onChange={() => setRadioOption('promote')}
              ouiaId="promote-radio-button"
            />
          </div>
        </AlertModal>
      )}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          aria-label={t`deletion error`}
          title={t`Error!`}
          onClose={() => setDeletionError(null)}
        >
          {t`Failed to delete one or more groups.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
};

InventoryGroupsDeleteModal.propTypes = {
  onAfterDelete: func.isRequired,
  groups: arrayOf(Group),
  isDisabled: bool.isRequired,
};

InventoryGroupsDeleteModal.defaultProps = {
  groups: [],
};

export default InventoryGroupsDeleteModal;
