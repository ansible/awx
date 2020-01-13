import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { OrganizationsAPI } from '@api';
import PaginatedDataList from '@components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '@util/qs';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function OrganizationTeams({ id, i18n }) {
  const location = useLocation();
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
      toolbarSearchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Created by (username)`),
          key: 'created_by__username',
        },
        {
          name: i18n._(t`Modified by (username)`),
          key: 'modified_by__username',
        },
      ]}
      toolbarSortColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name',
        },
      ]}
    />
  );
}

OrganizationTeams.propTypes = {
  id: PropTypes.number.isRequired,
};

export { OrganizationTeams as _OrganizationTeams };
export default withI18n()(OrganizationTeams);
