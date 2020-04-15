import getErrorMessage from './getErrorMessage';

describe('getErrorMessage', () => {
  test('should return data string', () => {
    const response = {
      data: 'error response',
    };
    expect(getErrorMessage(response)).toEqual('error response');
  });
  test('should return detail string', () => {
    const response = {
      data: {
        detail: 'detail string',
      },
    };
    expect(getErrorMessage(response)).toEqual('detail string');
  });
  test('should return an array of strings', () => {
    const response = {
      data: {
        project: ['project error response'],
      },
    };
    expect(getErrorMessage(response)).toEqual(['project error response']);
  });
  test('should consolidate error messages from multiple keys into an array', () => {
    const response = {
      data: {
        project: ['project error response'],
        inventory: ['inventory error response'],
        organization: ['org error response'],
      },
    };
    expect(getErrorMessage(response)).toEqual([
      'project error response',
      'inventory error response',
      'org error response',
    ]);
  });
  test('should handle no response.data', () => {
    const response = {};
    expect(getErrorMessage(response)).toEqual(null);
  });
  test('should consolidate multiple error messages from multiple keys into an array', () => {
    const response = {
      data: {
        project: ['project error response'],
        inventory: [
          'inventory error response',
          'another inventory error response',
        ],
      },
    };
    expect(getErrorMessage(response)).toEqual([
      'project error response',
      'inventory error response',
      'another inventory error response',
    ]);
  });
});
