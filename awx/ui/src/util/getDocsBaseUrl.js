export default function getDocsBaseUrl(config) {
  let version = 'latest';
  const licenseType = config?.license_info?.license_type;

  if (licenseType && licenseType !== 'open' && config?.version) {
    version = parseFloat(config?.version.split('-')[0]).toFixed(1);
  }

  return `https://docs.ansible.com/automation-controller/${version}`;
}
