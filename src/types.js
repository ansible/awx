import { shape, arrayOf, number, string, bool } from 'prop-types';

export const Role = shape({
  descendent_roles: arrayOf(string),
  role: shape({
    id: number.isRequired,
    name: string.isRequired,
    description: string,
    user_capabilities: shape({
      unattach: bool,
    }).isRequired,
  }),
});

export const AccessRecord = shape({
  id: number.isRequired,
  username: string.isRequired,
  url: string.isRequired,
  email: string,
  first_name: string,
  last_name: string,
  is_superuser: bool,
  is_system_auditor: bool,
  created: string,
  last_login: string,
  ldap_dn: string,
  related: shape({}),
  summary_fields: shape({
    direct_access: arrayOf(Role).isRequired,
    indirect_access: arrayOf(Role).isRequired,
  }).isRequired,
  type: string,
});

export const Organization = shape({
  id: number.isRequired,
  name: string.isRequired,
  custom_virtualenv: string, // ?
  description: string,
  max_hosts: number,
  related: shape(),
  summary_fields: shape({
    object_roles: shape(),
  }),
  type: string,
  url: string,
  created: string,
  modified: string,
});

export const QSConfig = shape({
  defaultParams: shape().isRequired,
  namespace: string,
  integerFields: arrayOf(string).isRequired,
});
