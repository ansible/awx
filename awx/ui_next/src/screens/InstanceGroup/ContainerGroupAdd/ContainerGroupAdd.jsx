import React, { useState, useEffect, useCallback } from 'react';
import { Card, PageSection } from '@patternfly/react-core';
import { useHistory } from 'react-router-dom';

import { CardBody } from '../../../components/Card';
import { InstanceGroupsAPI } from '../../../api';
import useRequest from '../../../util/useRequest';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import { jsonToYaml, isJsonString } from '../../../util/yaml';

import ContainerGroupForm from '../shared/ContainerGroupForm';

function ContainerGroupAdd() {
  const history = useHistory();
  const [submitError, setSubmitError] = useState(null);

  const getPodSpecValue = value => {
    if (isJsonString(value)) {
      value = jsonToYaml(value);
    }
    if (value !== jsonToYaml(JSON.stringify(initialPodSpec))) {
      return value;
    }
    return null;
  };

  const handleSubmit = async values => {
    try {
      const { data: response } = await InstanceGroupsAPI.create({
        name: values.name,
        credential: values?.credential?.id,
        pod_spec_override: values.override
          ? getPodSpecValue(values.pod_spec_override)
          : null,
      });
      history.push(`/instance_groups/container_group/${response.id}/details`);
    } catch (error) {
      setSubmitError(error);
    }
  };

  const handleCancel = () => {
    history.push(`/instance_groups`);
  };

  const {
    error: fetchError,
    isLoading,
    request: fetchInitialPodSpec,
    result: initialPodSpec,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InstanceGroupsAPI.readOptions();
      return data.actions.POST.pod_spec_override.default;
    }, []),
    {
      initialPodSpec: {},
    }
  );

  useEffect(() => {
    fetchInitialPodSpec();
  }, [fetchInitialPodSpec]);

  if (fetchError) {
    return (
      <PageSection>
        <Card>
          <CardBody>
            <ContentError error={fetchError} />
          </CardBody>
        </Card>
      </PageSection>
    );
  }

  if (isLoading) {
    return (
      <PageSection>
        <Card>
          <CardBody>
            <ContentLoading />
          </CardBody>
        </Card>
      </PageSection>
    );
  }

  return (
    <PageSection>
      <Card>
        <CardBody>
          <ContainerGroupForm
            initialPodSpec={initialPodSpec}
            onSubmit={handleSubmit}
            submitError={submitError}
            onCancel={handleCancel}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export default ContainerGroupAdd;
