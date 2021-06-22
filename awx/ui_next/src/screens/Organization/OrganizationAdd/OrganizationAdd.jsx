import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';
import useRequest from '../../../util/useRequest';
import { CredentialsAPI, OrganizationsAPI } from '../../../api';
import { CardBody } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import OrganizationForm from '../shared/OrganizationForm';

function OrganizationAdd() {
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const {
    isLoading,
    error: defaultGalaxyCredentialError,
    request: fetchDefaultGalaxyCredential,
    result: defaultGalaxyCredential,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await CredentialsAPI.read({
        credential_type__kind: 'galaxy',
        managed: true,
      });

      return results[0] || null;
    }, []),
    null
  );

  useEffect(() => {
    fetchDefaultGalaxyCredential();
  }, [fetchDefaultGalaxyCredential]);

  const handleSubmit = async (values, groupsToAssociate) => {
    try {
      const { data: response } = await OrganizationsAPI.create({
        ...values,
        default_environment: values.default_environment?.id,
      });
      await Promise.all(
        groupsToAssociate
          .map(id => OrganizationsAPI.associateInstanceGroup(response.id, id))
          .concat(
            values.galaxy_credentials.map(({ id: credId }) =>
              OrganizationsAPI.associateGalaxyCredential(response.id, credId)
            )
          )
      );
      history.push(`/organizations/${response.id}`);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push('/organizations');
  };

  if (defaultGalaxyCredentialError) {
    return (
      <PageSection>
        <Card>
          <CardBody>
            <ContentError error={defaultGalaxyCredentialError} />
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
          <OrganizationForm
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            submitError={formError}
            defaultGalaxyCredential={defaultGalaxyCredential}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { OrganizationAdd as _OrganizationAdd };
export default OrganizationAdd;
