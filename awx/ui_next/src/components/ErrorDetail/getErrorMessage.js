export default function getErrorMessage(response) {
  if (typeof response.data === 'string') {
    return response.data;
  }
  if (!response.data) {
    return null;
  }
  if (response.data.detail) {
    return response.data.detail;
  }
  return Object.values(response.data).reduce(
    (acc, currentValue) => acc.concat(currentValue),
    []
  );
}
