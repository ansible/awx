import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import { OrganizationsAPI } from '../../../api';
import { Config } from '../../../contexts/Config';

import NotificationTemplateForm from '../shared/NotificationTemplateForm';

function NotificationTemplateEdit({ template }) {
  const detailsUrl = `/notification_templates/${template.id}/details`;
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (
    values,
    groupsToAssociate,
    groupsToDisassociate
  ) => {
    try {
      await OrganizationsAPI.update(template.id, values);
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(template.id, id)
        )
      );
      await Promise.all(
        groupsToDisassociate.map(id =>
          OrganizationsAPI.disassociateInstanceGroup(template.id, id)
        )
      );
      history.push(detailsUrl);
    } catch (error) {
      setFormError(error);
    }
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  return (
    <CardBody>
      <Config>
        {({ me }) => (
          <NotificationTemplateForm
            template={template}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            me={me || {}}
            submitError={formError}
          />
        )}
      </Config>
    </CardBody>
  );
}

NotificationTemplateEdit.propTypes = {
  template: PropTypes.shape().isRequired,
};

NotificationTemplateEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { NotificationTemplateEdit as _NotificationTemplateEdit };
export default NotificationTemplateEdit;
