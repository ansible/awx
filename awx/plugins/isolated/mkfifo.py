import os
import stat

from ansible.module_utils.basic import AnsibleModule


#
# the purpose of this plugin is to call mkfifo and
# write raw SSH key data into the fifo created on the remote isolated host
#


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
        data = module.params['content']
        if 'OPENSSH PRIVATE KEY' in data and not data.endswith('\n'):
            # we use ansible's lookup() to read this file from the disk,
            # but ansible's lookup() *strips* newlines
            # OpenSSH wants certain private keys to end with a newline (or it
            # won't accept them)
            data += '\n'
        fifo.write(data)
    module.exit_json(dest=path, changed=True)


if __name__ == '__main__':
    main()
