// eslint-disable-next-line import/prefer-default-export
export function describeNotificationMixin (Model, name) {
  describe(name, () => {
    const mockHttp = ({ post: jest.fn(() => Promise.resolve()) });
    const ModelAPI = new Model(mockHttp);

    afterEach(() => {
      jest.clearAllMocks();
    });

    const parameters = ['success', 'error'];

    parameters.forEach((type) => {
      const label = `[notificationType=${type}, associationState=true`;
      const testName = `associateNotificationTemplate ${label} makes expected http calls`;

      test(testName, async (done) => {
        await ModelAPI.associateNotificationTemplate(1, 21, type);

        const expectedPath = `${ModelAPI.baseUrl}1/notification_templates_${type}/`;
        expect(mockHttp.post).toHaveBeenCalledTimes(1);

        const expectedParams = { id: 21 };
        expect(mockHttp.post.mock.calls.pop()).toEqual([expectedPath, expectedParams]);

        done();
      });
    });

    parameters.forEach((type) => {
      const label = `[notificationType=${type}, associationState=false`;
      const testName = `disassociateNotificationTemplate ${label} makes expected http calls`;

      test(testName, async (done) => {
        await ModelAPI.disassociateNotificationTemplate(1, 21, type);

        const expectedPath = `${ModelAPI.baseUrl}1/notification_templates_${type}/`;
        expect(mockHttp.post).toHaveBeenCalledTimes(1);

        const expectedParams = { id: 21, disassociate: true };
        expect(mockHttp.post.mock.calls.pop()).toEqual([expectedPath, expectedParams]);

        done();
      });
    });
  });
}
