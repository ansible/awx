import os
import stat

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            'path': {'required': True, 'type': 'str'},
            'content': {'required': True, 'type': 'str'}
        },
        supports_check_mode=False
    )

    path = module.params['path']
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    with open(path, 'w') as fifo:
        fifo.write(module.params['content'])
    module.exit_json(dest=path, changed=True)


if __name__ == '__main__':
    main()
