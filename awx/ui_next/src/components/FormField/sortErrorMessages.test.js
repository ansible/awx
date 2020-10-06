import sortErrorMessages from './sortErrorMessages';

describe('sortErrorMessages', () => {
  let consoleError;
  beforeEach(() => {
    consoleError = global.console.error;
    global.console.error = () => {};
  });

  afterEach(() => {
    global.console.error = consoleError;
  });

  test('should give general error message', () => {
    const error = {
      message: 'An error occurred',
    };
    const parsed = sortErrorMessages(error);

    expect(parsed).toEqual({
      formError: 'An error occurred',
      fieldErrors: null,
    });
  });

  test('should give field error messages', () => {
    const error = {
      response: {
        data: {
          foo: 'bar',
          baz: 'bam',
        },
      },
    };
    const parsed = sortErrorMessages(error, { foo: '', baz: '' });
    expect(parsed).toEqual({
      formError: '',
      fieldErrors: {
        foo: 'bar',
        baz: 'bam',
      },
    });
  });

  test('should give form error for nonexistent field', () => {
    const error = {
      response: {
        data: {
          alpha: 'oopsie',
          baz: 'bam',
        },
      },
    };
    const parsed = sortErrorMessages(error, { foo: '', baz: '' });
    expect(parsed).toEqual({
      formError: 'oopsie',
      fieldErrors: {
        baz: 'bam',
      },
    });
  });

  test('should join multiple field error messages', () => {
    const error = {
      response: {
        data: {
          foo: ['bar', 'bar2'],
          baz: 'bam',
        },
      },
    };
    const parsed = sortErrorMessages(error, { foo: '', baz: '' });
    expect(parsed).toEqual({
      formError: '',
      fieldErrors: {
        foo: 'bar; bar2',
        baz: 'bam',
      },
    });
  });
});
