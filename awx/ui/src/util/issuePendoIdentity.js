import { RootAPI, UsersAPI } from 'api';
import bootstrapPendo from './bootstrapPendo';

function buildPendoOptions(config, pendoApiKey) {
  const towerVersion = config.version.split('-')[0];
  const trial = config.trial ? config.trial : false;

  return {
    apiKey: pendoApiKey,
    visitor: {
      id: 0,
      role: null,
    },
    account: {
      id: 'tower.ansible.com',
      planLevel: config.license_type,
      planPrice: config.instance_count,
      creationDate: config.license_date,
      trial,
      tower_version: towerVersion,
      ansible_version: config.ansible_version,
    },
  };
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

async function issuePendoIdentity(config) {
  if (!('license_info' in config)) {
    config.license_info = {};
  }
  config.license_info.analytics_status = config.analytics_status;
  config.license_info.version = config.version;
  config.license_info.ansible_version = config.ansible_version;

  if (config.analytics_status !== 'off') {
    const {
      data: { PENDO_API_KEY },
    } = await RootAPI.readAssetVariables();
    if (PENDO_API_KEY && PENDO_API_KEY !== '') {
      bootstrapPendo(PENDO_API_KEY);
      const pendoOptions = buildPendoOptions(config, PENDO_API_KEY);
      const pendoOptionsWithRole = await buildPendoOptionsRole(
        pendoOptions,
        config
      );
      window.pendo.initialize(pendoOptionsWithRole);
    }
  }
}

export default issuePendoIdentity;
