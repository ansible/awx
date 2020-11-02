import 'styled-components/macro';
import React, { useState, useContext, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { func, bool, arrayOf, object } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Radio, DropdownItem } from '@patternfly/react-core';
import styled from 'styled-components';
import { KebabifiedContext } from '../../../contexts/Kebabified';
import { GroupsAPI, InventoriesAPI } from '../../../api';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';

const ListItem = styled.li`
  display: flex;
  font-weight: 600;
  color: var(--pf-global--danger-color--100);
`;

const InventoryGroupsDeleteModal = ({
  onAfterDelete,
  isDisabled,
  groups,
  i18n,
}) => {
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
  const handleDelete = async option => {
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
          aria-label={i18n._(t`Delete`)}
          onClick={() => setIsModalOpen(true)}
        >
          {i18n._(t`Delete`)}
        </DropdownItem>
      ) : (
        <Button
          variant="secondary"
          aria-label={i18n._(t`Delete`)}
          onClick={() => setIsModalOpen(true)}
          isDisabled={isDisabled || isDeleteLoading}
        >
          {i18n._(t`Delete`)}
        </Button>
      )}
      {isModalOpen && (
        <AlertModal
          isOpen={isModalOpen}
          variant="danger"
          title={
            groups.length > 1
              ? i18n._(t`Delete Groups?`)
              : i18n._(t`Delete Group?`)
          }
          onClose={() => setIsModalOpen(false)}
          actions={[
            <Button
              aria-label={i18n._(t`Confirm Delete`)}
              onClick={() => handleDelete(radioOption)}
              variant="danger"
              key="delete"
              isDisabled={radioOption === null}
            >
              {i18n._(t`Delete`)}
            </Button>,
            <Button
              aria-label={i18n._(t`Close`)}
              onClick={() => setIsModalOpen(false)}
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
        </AlertModal>
      )}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          aria-label={i18n._(t`deletion error`)}
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete one or more groups.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
};

InventoryGroupsDeleteModal.propTypes = {
  onAfterDelete: func.isRequired,
  groups: arrayOf(object),
  isDisabled: bool.isRequired,
};

InventoryGroupsDeleteModal.defaultProps = {
  groups: [],
};

export default withI18n()(InventoryGroupsDeleteModal);
