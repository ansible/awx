import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card, CardHeader, Tooltip } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import { Config } from '@contexts/Config';
import { CardBody } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';
import OrganizationForm from '../shared/OrganizationForm';

function OrganizationAdd({ i18n }) {
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (values, groupsToAssociate) => {
    try {
      const { data: response } = await OrganizationsAPI.create(values);
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(response.id, id)
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

  return (
    <PageSection>
      <Card>
        <CardHeader className="at-u-textRight">
          <Tooltip content={i18n._(t`Close`)} position="top">
            <CardCloseButton onClick={handleCancel} />
          </Tooltip>
        </CardHeader>
        <CardBody>
          <Config>
            {({ me }) => (
              <OrganizationForm
                onSubmit={handleSubmit}
                onCancel={handleCancel}
                me={me || {}}
              />
            )}
          </Config>
          {formError ? <div>error</div> : ''}
        </CardBody>
      </Card>
    </PageSection>
  );
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationAdd as _OrganizationAdd };
export default withI18n()(OrganizationAdd);
