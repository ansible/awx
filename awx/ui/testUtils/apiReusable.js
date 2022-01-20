// eslint-disable-next-line import/prefer-default-export
export function describeNotificationMixin (Model, name) {
  describe(name, () => {

    let mockHttp;
    let ModelAPI;
    beforeEach(() => {
      mockHttp = ({ post: jest.fn(() => Promise.resolve()) });
      ModelAPI = new Model(mockHttp);
    })

    afterEach(() => {
      jest.resetAllMocks();
    });

    const parameters = ['success', 'error'];

    parameters.forEach((type) => {
      const label = `[notificationType=${type}, associationState=true`;
      const testName = `associateNotificationTemplate ${label} makes expected http calls`;

      test(testName, async () => {
        await ModelAPI.associateNotificationTemplate(1, 21, type);

        const expectedPath = `${ModelAPI.baseUrl}1/notification_templates_${type}/`;
        expect(mockHttp.post).toHaveBeenCalledTimes(1);

        const expectedParams = { id: 21 };
        expect(mockHttp.post.mock.calls.pop()).toEqual([expectedPath, expectedParams]);

      });
    });

    parameters.forEach((type) => {
      const label = `[notificationType=${type}, associationState=false`;
      const testName = `disassociateNotificationTemplate ${label} makes expected http calls`;

      test(testName, async () => {
        await ModelAPI.disassociateNotificationTemplate(1, 21, type);

        const expectedPath = `${ModelAPI.baseUrl}1/notification_templates_${type}/`;
        expect(mockHttp.post).toHaveBeenCalledTimes(1);

        const expectedParams = { id: 21, disassociate: true };
        expect(mockHttp.post.mock.calls.pop()).toEqual([expectedPath, expectedParams]);

      });
    });
  });
}
