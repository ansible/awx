export default function getDocsBaseUrl(config) {
  let version = 'latest';
  const licenseType = config?.license_info?.license_type;

  if (licenseType && licenseType !== 'open') {
    if (config?.version) {
      if (parseFloat(config?.version.split('-')[0]) >= 4.3) {
        version = parseFloat(config?.version.split('-')[0]);
      } else {
        version = config?.version.split('-')[0];
      }
    }
  } else {
    version = 'latest';
  }
  return `https://docs.ansible.com/automation-controller/${version}`;
}
