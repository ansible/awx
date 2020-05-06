import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router-dom';
import { CardBody } from '../../../components/Card';

import { TeamsAPI } from '../../../api';
import { Config } from '../../../contexts/Config';

import TeamForm from '../shared/TeamForm';

function TeamEdit({ team }) {
  const history = useHistory();
  const [error, setError] = useState(null);

  const handleSubmit = async values => {
    try {
      await TeamsAPI.update(team.id, values);
      history.push(`/teams/${team.id}/details`);
    } catch (err) {
      setError(err);
    }
  };

  const handleCancel = () => {
    history.push(`/teams/${team.id}/details`);
  };

  return (
    <CardBody>
      <Config>
        {({ me }) => (
          <TeamForm
            team={team}
            handleSubmit={handleSubmit}
            handleCancel={handleCancel}
            me={me || {}}
            submitError={error}
          />
        )}
      </Config>
    </CardBody>
  );
}

TeamEdit.propTypes = {
  team: PropTypes.shape().isRequired,
};

TeamEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export default TeamEdit;
