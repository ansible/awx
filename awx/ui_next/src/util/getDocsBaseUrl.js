export default function getDocsBaseUrl(config) {
  let version = 'latest';
  if (config?.license_info?.license_type !== 'open') {
    version = config?.version ? config.version.split('-')[0] : 'latest';
  }
  return `https://docs.ansible.com/ansible-tower/${version}`;
}
