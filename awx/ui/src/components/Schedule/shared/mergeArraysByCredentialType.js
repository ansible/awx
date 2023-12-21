export default function mergeArraysByCredentialType(array1, array2) {
  const mergedArray = [...array1];

  array2.forEach((obj2) => {
    const index = mergedArray.findIndex(
      (obj1) => obj1.credential_type === obj2.credential_type
    );
    if (index !== -1) {
      mergedArray.splice(index, 1);
    }
    mergedArray.push(obj2);
  });

  return mergedArray;
}
