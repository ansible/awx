// eslint-disable-next-line import/prefer-default-export
export function describeNotificationMixin (Model, name) {
  describe(name, () => {
    const mockHttp = ({ post: jest.fn(() => Promise.resolve()) });
    const ModelAPI = new Model(mockHttp);

    afterEach(() => {
      jest.clearAllMocks();
    });

    const parameters = [
      ['success', true],
      ['success', false],
      ['error', true],
      ['error', false],
    ];
    parameters.forEach(([type, state]) => {
      const label = `[notificationType=${type}, associationState=${state}]`;
      const testName = `updateNotificationTemplateAssociation ${label} makes expected http calls`;

      test(testName, async (done) => {
        await ModelAPI.updateNotificationTemplateAssociation(1, 21, type, state);

        const expectedPath = `${ModelAPI.baseUrl}1/notification_templates_${type}/`;
        expect(mockHttp.post).toHaveBeenCalledTimes(1);

        const expectedParams = state ? { id: 21 } : { id: 21, disassociate: true };
        expect(mockHttp.post.mock.calls.pop()).toEqual([expectedPath, expectedParams]);

        done();
      });
    });
  });
}
