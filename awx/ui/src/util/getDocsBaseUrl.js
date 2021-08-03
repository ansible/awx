export default function getDocsBaseUrl(config) {
  let version = 'latest';
  const licenseType = config?.license_info?.license_type;
  if (licenseType && licenseType !== 'open') {
    version = config?.version ? config.version.split('-')[0] : 'latest';
  }
  return `https://docs.ansible.com/automation-controller/${version}`;
}
