import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Inventory } from 'types';
import useRequest from 'hooks/useRequest';
import { InventoriesAPI } from 'api';
import { CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import SmartInventoryForm from '../shared/SmartInventoryForm';
import parseHostFilter from '../shared/utils';

function SmartInventoryEdit({ inventory }) {
  const history = useHistory();
  const detailsUrl = `/inventories/smart_inventory/${inventory.id}/details`;

  const {
    error: contentError,
    isLoading: hasContentLoading,
    request: fetchInstanceGroups,
    result: initialInstanceGroups,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await InventoriesAPI.readInstanceGroups(inventory.id);
      return results;
    }, [inventory.id]),
    []
  );

  useEffect(() => {
    fetchInstanceGroups();
  }, [fetchInstanceGroups]);

  const {
    error: submitError,
    request: submitRequest,
    result: submitResult,
  } = useRequest(
    useCallback(
      async (values, groupsToAssociate, groupsToDisassociate) => {
        const { data } = await InventoriesAPI.update(inventory.id, values);
        await InventoriesAPI.orderInstanceGroups(
          inventory.id,
          groupsToAssociate,
          groupsToDisassociate
        );
        return data;
      },
      [inventory.id]
    )
  );

  useEffect(() => {
    if (submitResult) {
      history.push({
        pathname: detailsUrl,
        search: '',
      });
    }
  }, [submitResult, detailsUrl, history]);

  const handleSubmit = async (form) => {
    const modifiedForm = parseHostFilter(form);
    const { instance_groups, organization, ...remainingForm } = modifiedForm;

    await submitRequest(
      {
        organization: organization?.id,
        ...remainingForm,
      },
      instance_groups,
      initialInstanceGroups
    );
  };

  const handleCancel = () => {
    history.push({
      pathname: detailsUrl,
      search: '',
    });
  };

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <SmartInventoryForm
        inventory={inventory}
        instanceGroups={initialInstanceGroups}
        onCancel={handleCancel}
        onSubmit={handleSubmit}
        submitError={submitError}
      />
    </CardBody>
  );
}

SmartInventoryEdit.propTypes = {
  inventory: Inventory.isRequired,
};

export default SmartInventoryEdit;
