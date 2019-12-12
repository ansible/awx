import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';

import { OrganizationsAPI } from '@api';
import PaginatedDataList from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function OrganizationTeams({ id, location }) {
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(false);
  const [itemCount, setItemCount] = useState(0);
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    (async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { count = 0, results = [] },
        } = await OrganizationsAPI.readTeams(id, params);
        setItemCount(count);
        setTeams(results);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [id, location]);

  return (
    <PaginatedDataList
      contentError={contentError}
      hasContentLoading={hasContentLoading}
      items={teams}
      itemCount={itemCount}
      pluralizedItemName="Teams"
      qsConfig={QS_CONFIG}
    />
  );
}

OrganizationTeams.propTypes = {
  id: PropTypes.number.isRequired,
};

export { OrganizationTeams as _OrganizationTeams };
export default withRouter(OrganizationTeams);
