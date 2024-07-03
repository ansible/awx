import ConstructedInventories from './ConstructedInventories';

describe('ConstructedInventoriesAPI', () => {
  const constructedInventoryId = 1;
  const constructedInventoryMethod = 'PUT';
  let ConstructedInventoriesAPI;
  let mockHttp;

  beforeEach(() => {
    const optionsPromise = () =>
      Promise.resolve({
        data: {
          actions: {
            PUT: {},
          },
        },
      });
    mockHttp = {
      options: jest.fn(optionsPromise),
    };
    ConstructedInventoriesAPI = new ConstructedInventories(mockHttp);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('readConstructedInventoryOptions calls options with the expected params', async () => {
    await ConstructedInventoriesAPI.readConstructedInventoryOptions(
      constructedInventoryId,
      constructedInventoryMethod
    );
    expect(mockHttp.options).toHaveBeenCalledTimes(1);
    expect(mockHttp.options).toHaveBeenCalledWith(
      `api/v2/constructed_inventories/${constructedInventoryId}/`
    );
  });

  test('readConstructedInventory should throw an error if action method is missing', async () => {
    try {
      await ConstructedInventoriesAPI.readConstructedInventoryOptions(
        constructedInventoryId,
        'POST'
      );
    } catch (error) {
      expect(error.message).toContain(
        'You have insufficient access to this Constructed Inventory.'
      );
    }
  });
});
