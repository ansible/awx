import getEventRequestParams, { range } from './getEventRequestParams';

describe('getEventRequestParams', () => {
  const job = {
    status: 'successful',
  };

  it('should return first page', () => {
    const [params, loadRange] = getEventRequestParams(job, 50, [1, 50]);

    expect(params).toEqual({
      page: 1,
      page_size: 50,
    });
    expect(loadRange).toEqual(range(1, 50));
  });

  it('should return second page', () => {
    const [params, loadRange] = getEventRequestParams(job, 1000, [51, 100]);

    expect(params).toEqual({
      page: 2,
      page_size: 50,
    });
    expect(loadRange).toEqual(range(51, 100));
  });

  it('should return page for first portion of requested range', () => {
    const [params, loadRange] = getEventRequestParams(job, 1000, [75, 125]);

    expect(params).toEqual({
      page: 2,
      page_size: 50,
    });
    expect(loadRange).toEqual(range(51, 100));
  });

  it('should return smaller page for shorter range', () => {
    const [params, loadRange] = getEventRequestParams(job, 1000, [120, 125]);

    expect(params).toEqual({
      page: 21,
      page_size: 6,
    });
    expect(loadRange).toEqual(range(121, 126));
  });

  it('should return last event only', () => {
    const [params, loadRange] = getEventRequestParams(job, 72, [72, 72]);

    expect(params).toEqual({
      page: 72,
      page_size: 1,
    });
    expect(loadRange).toEqual(range(72, 72));
  });
});
