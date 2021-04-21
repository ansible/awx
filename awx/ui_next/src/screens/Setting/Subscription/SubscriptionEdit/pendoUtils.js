import { UsersAPI } from '../../../../api';
import bootstrapPendo from './bootstrapPendo';

function buildPendoOptions(config, pendoApiKey) {
  const tower_version = config.version.split('-')[0];
  const trial = config.trial ? config.trial : false;
  const options = {
    apiKey: pendoApiKey,
    visitor: {
      id: null,
      role: null,
    },
    account: {
      id: null,
      planLevel: config.license_type,
      planPrice: config.instance_count,
      creationDate: config.license_date,
      trial,
      tower_version,
      ansible_version: config.ansible_version,
    },
  };

  options.visitor.id = 0;
  options.account.id = 'tower.ansible.com';

  return options;
}

async function buildPendoOptionsRole(options, config) {
  try {
    if (config.me.is_superuser) {
      options.visitor.role = 'admin';
    } else {
      const { data } = await UsersAPI.readAdminOfOrganizations(config.me.id);
      if (data.count > 0) {
        options.visitor.role = 'orgadmin';
      } else {
        options.visitor.role = 'user';
      }
    }
    return options;
  } catch (error) {
    throw new Error(error);
  }
}

async function issuePendoIdentity(config, pendoApiKey) {
  config.license_info.analytics_status = config.analytics_status;
  config.license_info.version = config.version;
  config.license_info.ansible_version = config.ansible_version;

  if (config.analytics_status !== 'off') {
    bootstrapPendo(pendoApiKey);
    const pendoOptions = buildPendoOptions(config, pendoApiKey);
    const pendoOptionsWithRole = await buildPendoOptionsRole(
      pendoOptions,
      config
    );
    window.pendo.initialize(pendoOptionsWithRole);
  }
}

export default issuePendoIdentity;
