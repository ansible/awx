import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Card } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import useRequest from 'hooks/useRequest';
import { InventorySourcesAPI } from 'api';
import InventorySourceForm from '../shared/InventorySourceForm';

function InventorySourceEdit({ source, inventory }) {
  const history = useHistory();
  const { id, organization } = inventory;
  const detailsUrl = `/inventories/inventory/${id}/sources/${source.id}/details`;

  const { error, request, result } = useRequest(
    useCallback(
      async (values) => {
        const { data } = await InventorySourcesAPI.replace(source.id, values);
        return data;
      },
      [source.id]
    ),
    null
  );

  useEffect(() => {
    if (result) {
      history.push(detailsUrl);
    }
  }, [result, detailsUrl, history]);

  const handleSubmit = async (form) => {
    const {
      credential,
      source_path,
      source_project,
      source_script,
      execution_environment,
      ...remainingForm
    } = form;

    const sourcePath = {};
    const sourceProject = {};
    if (form.source === 'scm') {
      sourcePath.source_path =
        source_path === '/ (project root)' ? '' : source_path;
      sourceProject.source_project = source_project.id;
    }

    await request({
      credential: credential?.id || null,
      inventory: id,
      source_script: source_script?.id || null,
      execution_environment: execution_environment?.id || null,
      ...sourcePath,
      ...sourceProject,
      ...remainingForm,
    });
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  return (
    <Card>
      <CardBody>
        <InventorySourceForm
          source={source}
          onCancel={handleCancel}
          onSubmit={handleSubmit}
          submitError={error}
          organizationId={organization}
        />
      </CardBody>
    </Card>
  );
}

export default InventorySourceEdit;
