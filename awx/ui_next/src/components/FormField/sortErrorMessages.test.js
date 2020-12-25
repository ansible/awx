import sortErrorMessages from './sortErrorMessages';

describe('sortErrorMessages', () => {
  let consoleError;
  beforeEach(() => {
    // Component logs errors to console. Hide those during testing.
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

  test('should give nested field error messages', () => {
    const error = {
      response: {
        data: {
          inputs: {
            url: ['URL Error'],
            other: {
              stuff: ['Other stuff error'],
            },
          },
        },
      },
    };
    const formValues = {
      inputs: {
        url: '',
        other: {
          stuff: '',
        },
      },
    };
    const parsed = sortErrorMessages(error, formValues);
    expect(parsed).toEqual({
      formError: '',
      fieldErrors: {
        inputs: {
          url: 'URL Error',
          other: {
            stuff: 'Other stuff error',
          },
        },
      },
    });
  });

  test('should give unknown nested field error as form error', () => {
    const error = {
      response: {
        data: {
          inputs: {
            url: ['URL Error'],
            other: {
              stuff: ['Other stuff error'],
            },
          },
        },
      },
    };
    const formValues = {
      inputs: {
        url: '',
      },
    };
    const parsed = sortErrorMessages(error, formValues);
    expect(parsed).toEqual({
      formError: 'Other stuff error',
      fieldErrors: {
        inputs: {
          url: 'URL Error',
        },
      },
    });
  });
});
