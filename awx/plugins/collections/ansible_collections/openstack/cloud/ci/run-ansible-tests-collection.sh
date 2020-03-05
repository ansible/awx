#!/bin/bash
#############################################################################
# run-ansible-tests.sh
#
# Script used to setup a tox environment for running Ansible. This is meant
# to be called by tox (via tox.ini). To run the Ansible tests, use:
#
#    tox -e ansible [TAG ...]
# or
#    tox -e ansible -- -c cloudX [TAG ...]
# or to use the development version of Ansible:
#    tox -e ansible -- -d -c cloudX [TAG ...]
#
# USAGE:
#    run-ansible-tests.sh -e ENVDIR [-d] [-c CLOUD] [TAG ...]
#
# PARAMETERS:
#    -d         Use Ansible source repo development branch.
#    -e ENVDIR  Directory of the tox environment to use for testing.
#    -c CLOUD   Name of the cloud to use for testing.
#               Defaults to "devstack-admin".
#    [TAG ...]  Optional list of space-separated tags to control which
#               modules are tested.
#
# EXAMPLES:
#    # Run all Ansible tests
#    run-ansible-tests.sh -e ansible
#
#    # Run auth, keypair, and network tests against cloudX
#    run-ansible-tests.sh -e ansible -c cloudX auth keypair network
#############################################################################
set -ex

CLOUD="devstack-admin"
ENVDIR=
USE_DEV=0

while getopts "c:de:" opt
do
    case $opt in
    d) USE_DEV=1 ;;
    c) CLOUD=${OPTARG} ;;
    e) ENVDIR=${OPTARG} ;;
    ?) echo "Invalid option: -${OPTARG}"
       exit 1;;
    esac
done

if [ -z ${ENVDIR} ]
then
    echo "Option -e is required"
    exit 1
fi

shift $((OPTIND-1))
TAGS=$( echo "$*" | tr ' ' , )

# We need to source the current tox environment so that Ansible will
# be setup for the correct python environment.
source $ENVDIR/bin/activate

if [ ${USE_DEV} -eq 1 ]
then
    if [ -d ${ENVDIR}/ansible ]
    then
        echo "Using existing Ansible source repo"
    else
        echo "Installing Ansible source repo at $ENVDIR"
        git clone --recursive https://github.com/ansible/ansible.git ${ENVDIR}/ansible
    fi
    source $ENVDIR/ansible/hacking/env-setup
fi

# Run the shade Ansible tests
tag_opt=""
if [ ! -z ${TAGS} ]
then
    tag_opt="--tags ${TAGS}"
fi

# Loop through all ANSIBLE_VAR_ environment variables to allow passing the further
for var in $(env | grep -e '^ANSIBLE_VAR_'); do
  VAR_NAME=${var%%=*} # split variable name from value
  ANSIBLE_VAR_NAME=${VAR_NAME#ANSIBLE_VAR_} # cut ANSIBLE_VAR_ prefix from variable name
  ANSIBLE_VAR_NAME=${ANSIBLE_VAR_NAME,,} # lowercase ansible variable
  ANSIBLE_VAR_VALUE=${!VAR_NAME} # Get the variable value
  ANSIBLE_VARS+="${ANSIBLE_VAR_NAME}=${ANSIBLE_VAR_VALUE} " # concat variables
done

# Until we have a module that lets us determine the image we want from
# within a playbook, we have to find the image here and pass it in.
# We use the openstack client instead of nova client since it can use clouds.yaml.
IMAGE=`openstack --os-cloud=${CLOUD} image list -f value -c Name | grep cirros | grep -v -e ramdisk -e kernel`
if [ $? -ne 0 ]
then
  echo "Failed to find Cirros image"
  exit 1
fi

# install collections
tox -ebuild
ansible-galaxy collection build --force . --output-path ./build_artifact
ansible-galaxy collection install $(ls build_artifact/openstack-cloud-*) --force
pushd ci/
# run tests
ANSIBLE_COLLECTIONS_PATHS=${HOME}/.ansible/collections ansible-playbook -vvv ./run-collection.yml -e "cloud=${CLOUD} image=${IMAGE} ${ANSIBLE_VARS}" ${tag_opt}
popd
