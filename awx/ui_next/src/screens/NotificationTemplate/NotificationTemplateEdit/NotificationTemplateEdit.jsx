import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import { NotificationTemplatesAPI } from '../../../api';
import NotificationTemplateForm from '../shared/NotificationTemplateForm';

function NotificationTemplateEdit({ template, defaultMessages }) {
  const detailsUrl = `/notification_templates/${template.id}/details`;
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleSubmit = async values => {
    try {
      await NotificationTemplatesAPI.update(template.id, values);
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
      <NotificationTemplateForm
        template={template}
        defaultMessages={defaultMessages}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitError={formError}
      />
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
