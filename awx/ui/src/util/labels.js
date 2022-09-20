import { LabelsAPI, OrganizationsAPI } from '../api';

async function createNewLabels(labels = [], organization = null) {
  let error = null;
  const labelIds = [];

  try {
    const newLabels = [];
    const labelRequests = [];
    let organizationId = organization;
    if (labels) {
      labels.forEach((label) => {
        if (typeof label.id !== 'number') {
          newLabels.push(label);
        } else {
          labelIds.push(label.id);
        }
      });
    }

    if (newLabels.length > 0) {
      if (!organizationId) {
        // eslint-disable-next-line no-useless-catch
        try {
          const {
            data: { results },
          } = await OrganizationsAPI.read();
          organizationId = results[0].id;
        } catch (err) {
          throw err;
        }
      }
    }

    newLabels.forEach((label) => {
      labelRequests.push(
        LabelsAPI.create({
          name: label.name,
          organization: organizationId,
        }).then(({ data }) => {
          labelIds.push(data.id);
        })
      );
    });

    await Promise.all(labelRequests);
  } catch (err) {
    error = err;
  }

  return {
    labelIds,
    error,
  };
}

export default createNewLabels;
