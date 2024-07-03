export default function mergeArraysByCredentialType(
  defaultCredentials = [],
  overrides = []
) {
  const mergedArray = [...defaultCredentials];

  overrides.forEach((override) => {
    const index = mergedArray.findIndex(
      (defaultCred) => defaultCred.credential_type === override.credential_type
    );
    if (index !== -1) {
      mergedArray.splice(index, 1);
    }
    mergedArray.push(override);
  });

  return mergedArray;
}
