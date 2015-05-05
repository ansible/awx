## How I will do it

1. Find all facts from results
2. Filter out all "same facts"
3. Transform for display

### Finding facts from results

Iterate over fact collection. Check if a thing is a fact or not (it is a fact when all of its key's values are comparable (not an object or array). If it's a fact, then transform it to an object that contains the nested key and value from each candidate. If it's not a fact, then recurse passing in the parent keys & value until we find a fact.

To accomplish this we'll reduce over the values in the fact collection to create a new array. For each key, we'll check the type of its value. If it's an object or an array, we'll append the key to an array of parent keys and pass that and the value into a recursive call. If it's not an object or array, we'll record the parent key path as an array & both left & right values. We'll return the accumulator array with that object concatenated to it.

End result example (FactComparison):

[{  keyPath: ['sda', 'partitions', 'sda1'],
    key: 'sectors',
    leftValue: '39843840',
    rightValue: '13254121'
 },
 {  keyPath: ['sda', partitions', 'sda1'],
    key: 'model',
    leftValue: 'VMware Virtual S",
    rightValue: ''
 }];

### Filtering out "same" facts

This needs to look at all of the facts by parent key and remove any of those that have one or more differences. This will leave plenty of context for the user to determine exactly what is different here. For example, given the facts:

#### Left Host

```json
{   "ansible_mounts":
    [{
        "device": "/dev/sda1",
        "fstype": "ext4",
        "mount": "/",
        "options": "rw,errors=remount-ro",
        "size_available": 15032406016,
        "size_total": 20079898624
    }]
}
```

#### Right Host

```json
{   "ansible_mounts":
    [{
        "device": "/dev/sda1",
        "fstype": "btrfs",
        "mount": "/",
        "options": "rw,errors=remount-ro",
        "size_available": 153985231054,
        "size_total": 53056978564321
    }]
}
```

If all the user could see was that the `fstype` fields were different, this would leave them wondering "what device is that on? where did that come from?" We are solving this problem by displaying all sibling properties of a fact regardless of whether they are different when at least one of those properties contains a difference.

Therefore, to compare facts we need to first group them by their keys. Once we do that, we'll have a structure like:

```json
{   'sda.partitions.sda1':
    [{  keyPath: ['sda', 'partitions', 'sda1'],
        key: 'sectors',
        leftValue: '39843840',
        rightValue: '13254121'
     },
     {  keyPath: ['sda', partitions', 'sda1'],
        key: 'model',
        leftValue: 'VMware Virtual S",
        rightValue: ''
     }]
}
```

The simplest way to handle this would be to map over each key in this grouped object and return a filtered array of only objects with differences. Then we could iterate over the resulting object and filter out any keys whose value is an empty array, leaving us with only the keys that contain at least a single difference. Finally, we iterate over the original collection keeping only those values whose `keyPath` is in the previous collection of keys and return that result.

### Transforming for display

Given fact comparisons of:

[{  keyPath: ['ansible_devices', 'sda'],
    key: 'host',
    leftValue: 'SCSI storage controller: LSI Logic / Symbios Logic 53c1030 PCI-X Fusion-MPT Dual Ultra320 SCSI (rev 01)',
    rightValue: ''

 },
 {  keyPath: ['ansible_devices', 'sda'],
    key: 'model',
    leftValue: 'VMWare Virtual S',
    rightValue: 'APPLE SSD SM256C'
 },
 {  keyPath: ['ansible_devices', 'sda', 'partitions', 'sda1'],
    key: 'sectors',
    leftValue: '39843840',
    rightValue: '13254121'
 },
 {  keyPath: ['ansible_devices', 'sda', partitions', 'sda1'],
    key: 'sectorsize',
    leftValue: '512',
    rightValue: '512'
 },
 {  keyPath: ['ansible_mounts', '0'],
    key: 'device',
    leftValue: '/dev/sda5',
    rightValue: '/dev/sda1'
 },
 {  keyPath: ['ansible_mounts', '0'],
    key: 'fstype',
    leftValue: 'ext4',
    rightValue: 'btrfs'
 },
 {  keyPath: ['ansible_mounts', '1'],
    key: 'device',
    leftValue: 'absent',
    rightValue: '/dev/sda5'
 }];

We need to transform that to something like:

[{  keyPath: ['ansible_devices', 'sda'],
    displayKeyPath: 'ansible_devices.sda',
    nestingLevel: 1,
    facts:
    [{  keyPath: ['ansible_devices', 'sda'],
        key: 'host',
        value1: 'SCSI storage controller: LSI Logic / Symbios Logic 53c1030 PCI-X Fusion-MPT Dual Ultra320 SCSI (rev 01)',
        value2: ''

     },
     {  keyPath: ['ansible_devices', 'sda'],
        keyName: 'model',
        value1: 'VMWare Virtual S',
        value2: 'APPLE SSD SM256C'
     }],
 },
 {  keyPath: ['ansible_devices', 'sda', 'partitions', 'sda1'],
    displayKeyPath: 'partitions.sda1',
    nestingLevel: 2,
    facts:
    // ...
 },
 {   keyPath: ['ansible_mounts'],
     displayKeyPath: 'ansible_mounts',
     nestingLevel: 1,
     isArray: true,
     facts:
     [   [{  keyPath: ['ansible_mounts', '0'],
            key: 'device',
            leftValue: '/dev/sda5',
            rightValue: '/dev/sda1'
          },
          {  keyPath: ['ansible_mounts', '0'],
             key: 'fstype',
             leftValue: 'ext4',
             rightValue: 'btrfs'
          }],
         [{  keyPath: ['ansible_mounts', '1'],
             key: 'device',
             leftValue: 'absent',
             rightValue: '/dev/sda5'
          }]
     ]
 }]
```
