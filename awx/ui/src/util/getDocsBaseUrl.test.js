import getDocsBaseUrl from './getDocsBaseUrl';

describe('getDocsBaseUrl', () => {
  it('should return latest version for open license', () => {
    const result = getDocsBaseUrl({
      license_info: {
        license_type: 'open',
      },
      version: '18.4.4',
    });

    expect(result).toEqual(
      'https://docs.ansible.com/automation-controller/latest'
    );
  });

  it('should return current version for enterprise license', () => {
    const result = getDocsBaseUrl({
      license_info: {
        license_type: 'enterprise',
      },
      version: '18.4.4',
    });

    expect(result).toEqual(
      'https://docs.ansible.com/automation-controller/18.4'
    );
  });

  it('should strip version info after hyphen', () => {
    const result = getDocsBaseUrl({
      license_info: {
        license_type: 'enterprise',
      },
      version: '7.0.0-beta',
    });

    expect(result).toEqual(
      'https://docs.ansible.com/automation-controller/7.0'
    );
  });

  it('should return latest version if license info missing', () => {
    const result = getDocsBaseUrl({
      version: '18.4.4',
    });

    expect(result).toEqual(
      'https://docs.ansible.com/automation-controller/latest'
    );
  });
});
