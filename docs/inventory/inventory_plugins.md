# Transition to Ansible Inventory Plugins

For cloud inventory sources (such as ec2, gce, etc.) inventory updates changed from using deprecated inventory scripts, to using YAML files which are parsed by their respective inventory plugin.

Regardless of whether Ansible 2.9 or later is used, AWX should use the inventory plugin from the collection inside of the execution environment where the inventory update runs. The needed collections are in the AWX default execution environment:

https://github.com/ansible/awx-ee


### Switch to Ansible Inventory

The CLI entry point `ansible-inventory` was introduced in Ansible 2.4. Inventory imports run this command as an intermediary between the inventory and the import's logic to save content to the database. Using `ansible-inventory` eliminates the need to maintain source-specific logic, relying on Ansible's code instead. This also enables consistent data structure output from `ansible-inventory`.


## Writing Your Own Inventory File

You can add an SCM inventory source that points to your own yaml file which specifies an inventory plugin. You can also apply a credential of a `managed` type to that inventory source that matches the credential you are using. For example, you could have an inventory file for the `amazon.aws.aws_ec2` plugin and use the built-in `aws` credential type.

All built-in sources provide _secrets_ via environment variables.  These can be re-used for SCM-based inventory, and your inventory file can be used to specify non-sensitive configuration details such as the `keyed_groups` (to provide) or `hostvars` (to construct).

## Required IAM Permissions for the `aws_ec2` Inventory Plugin

An inventory source that uses the `amazon.aws.aws_ec2` plugin authenticates to AWS with a credential of the built-in `aws` type, or with an IAM instance profile attached to the control node. The IAM role behind that credential must be allowed to perform the API actions the plugin calls. When the role does not have permission for one of those actions, the plugin raises a 403 (Forbidden) error and the inventory update fails, which is why the required actions are easy to miss.

With the inventory file left at its defaults, the plugin makes two EC2 API calls per region:

- `ec2:DescribeInstances` is always called to fetch the instance list. Instance tags, public and private addresses, and placement information are all returned by this call, so `ec2:DescribeTags` is not needed for the plugin to work.
- `ec2:DescribeAvailabilityZones` is called unconditionally to populate the `placement.availability_zone_id` host variable. This call was added in `amazon.aws` 12.0.0. If the inventory file does not set `regions`, the plugin also calls `ec2:DescribeRegions` to discover which regions to query; that call tolerates a 403 and only produces a warning, so it is safe to omit from the policy.

The following policy is sufficient for a basic `aws_ec2` inventory in the regions being queried:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AWXEc2Inventory",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeAvailabilityZones"
            ],
            "Resource": "*"
        }
    ]
}
```

If the execution environment ships an older `amazon.aws` collection that predates `amazon.aws` 12.0.0, `ec2:DescribeAvailabilityZones` is not called and the `ec2:DescribeInstances` action alone is enough.

The options `use_ssm_inventory` and `route53_enabled` default to false, and the additional permissions they require are only needed when you enable them:

- `use_ssm_inventory: true` additionally requires `ssm:GetInventory`.
- `route53_enabled: true` additionally requires `route53:ListHostedZones` and `route53:ListResourceRecordSets`.

`strict_permissions` defaults to true, so any permission error causes the inventory update to fail. Setting `strict_permissions: false` makes the plugin skip 403 errors instead of failing, which is useful when the role lacks some of the optional permissions and you do not need the data they provide.

The policy above uses `"Resource": "*"`. `ec2:DescribeInstances` can be scoped to specific instance ARNs instead, if you want to tighten the role. For a broader set of actions used when the `aws_ec2` plugin is combined with the other inventory plugins in the `amazon.aws` collection, see the [aws_ec2 plugin documentation](https://docs.ansible.com/projects/ansible/latest/collections/amazon/aws/aws_ec2_inventory.html). The `amazon.aws.aws_rds` plugin, for example, additionally requires `rds:DescribeDBInstances` and `rds:ListTagsForResource`.
