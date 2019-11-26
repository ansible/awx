import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import AlertModal from '@components/AlertModal';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Radio } from '@patternfly/react-core';
import styled from 'styled-components';

const ListItem = styled.div`
  padding: 24px 1px;

  dl {
    display: flex;
    font-weight: 600;
  }
  dt {
    color: var(--pf-global--danger-color--100);
    margin-right: 10px;
  }
  .pf-c-radio {
    margin-top: 10px;
  }
`;

const ContentWrapper = styled.div`
  ${ListItem} + ${ListItem} {
    border-top-width: 1px;
    border-top-style: solid;
    border-top-color: #d7d7d7;
  }
  ${ListItem}:last-child {
    padding-bottom: 0;
  }
 `;

const InventoryGroupsDeleteModal = ({
  onClose,
  onDelete,
  isModalOpen,
  groups,
  i18n,
}) => {
  const [deleteList, setDeleteList] = useState([]);

  useEffect(() => {
    const groupIds = groups.reduce((obj, group) => {
      if (group.total_groups > 0 || group.total_hosts > 0) {
        return { ...obj, [group.id]: null };
      }
      return { ...obj, [group.id]: 'delete' };
    }, {});

    setDeleteList(groupIds);
  }, [groups]);

  const handleChange = (groupId, radioOption) => {
    setDeleteList({ ...deleteList, [groupId]: radioOption });
  };

  const content = groups
    .map(group => {
      if (group.total_groups > 0 || group.total_hosts > 0) {
        return (
          <ListItem key={group.id}>
            <dl>
              <dt>{group.name}</dt>
              <dd>
                {i18n._(
                  t`(${group.total_groups} Groups and ${group.total_hosts} Hosts)`
                )}
              </dd>
            </dl>
            <Radio
              key="radio-delete"
              label={i18n._(t`Delete All Groups and Hosts`)}
              id={`radio-delete-${group.id}`}
              name={`radio-${group.id}`}
              onChange={() => handleChange(group.id, 'delete')}
            />
            <Radio
              key="radio-promote"
              label={i18n._(t`Promote Child Groups and Hosts`)}
              id={`radio-promote-${group.id}`}
              name={`radio-${group.id}`}
              onChange={() => handleChange(group.id, 'promote')}
            />
          </ListItem>
        );
      }
      return (
        <ListItem key={group.id}>
          <dl>
            <dt>{group.name}</dt>
            <dd>{i18n._(t`(No Child Groups or Hosts)`)}</dd>
          </dl>
        </ListItem>
      );
    })
    .reduce((array, el) => {
      return array.concat(el);
    }, []);

  return ReactDOM.createPortal(
    <AlertModal
      isOpen={isModalOpen}
      variant="danger"
      title={
        groups.length > 1 ? i18n._(t`Delete Groups`) : i18n._(t`Delete Group`)
      }
      onClose={onClose}
      actions={[
        <Button
          aria-label={i18n._(t`Delete`)}
          onClick={() => onDelete(deleteList)}
          variant="danger"
          key="delete"
          isDisabled={Object.keys(deleteList).some(
            group => deleteList[group] === null
          )}
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
      <ContentWrapper>{content}</ContentWrapper>
    </AlertModal>,
    document.body
  );
};

export default withI18n()(InventoryGroupsDeleteModal);
