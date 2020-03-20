import React, { Fragment, useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Modal } from '@patternfly/react-core';
import OptionsList from '@components/Lookup/shared/OptionsList';
import useRequest from '@util/useRequest';
import { getQSConfig, parseQueryString } from '@util/qs';
import useSelected from '@util/useSelected';

const QS_CONFIG = getQSConfig('associate', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function AssociateModal({
  i18n,
  header = i18n._(t`Items`),
  title = i18n._(t`Select Items`),
  onClose,
  onAssociate,
  fetchRequest,
  isModalOpen = false,
}) {
  const history = useHistory();
  const { selected, handleSelect } = useSelected([]);

  const {
    request: fetchItems,
    result: { items, itemCount },
    error: contentError,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const {
        data: { count, results },
      } = await fetchRequest(params);

      return {
        items: results,
        itemCount: count,
      };
    }, [fetchRequest, history.location.search]),
    {
      items: [],
      itemCount: 0,
    }
  );

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const clearQSParams = () => {
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const ns = QS_CONFIG.namespace;
    const otherParts = parts.filter(param => !param.startsWith(`${ns}.`));
    history.replace(`${history.location.pathname}?${otherParts.join('&')}`);
  };

  const handleSave = async () => {
    await onAssociate(selected);
    clearQSParams();
    onClose();
  };

  const handleClose = () => {
    clearQSParams();
    onClose();
  };

  return (
    <Fragment>
      <Modal
        isFooterLeftAligned
        isLarge
        title={title}
        isOpen={isModalOpen}
        onClose={handleClose}
        actions={[
          <Button
            aria-label={i18n._(t`Save`)}
            key="select"
            variant="primary"
            onClick={handleSave}
            isDisabled={selected.length === 0}
          >
            {i18n._(t`Save`)}
          </Button>,
          <Button
            aria-label={i18n._(t`Cancel`)}
            key="cancel"
            variant="secondary"
            onClick={handleClose}
          >
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        <OptionsList
          contentError={contentError}
          deselectItem={handleSelect}
          header={header}
          isLoading={isLoading}
          multiple
          optionCount={itemCount}
          options={items}
          qsConfig={QS_CONFIG}
          readOnly={false}
          selectItem={handleSelect}
          value={selected}
          searchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
              isDefault: true,
            },
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username',
            },
          ]}
          sortColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
            },
          ]}
        />
      </Modal>
    </Fragment>
  );
}

export default withI18n()(AssociateModal);
