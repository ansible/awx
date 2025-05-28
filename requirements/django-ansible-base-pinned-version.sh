#!/bin/bash
set +x

# CONSTANTS
export REGEX_LEFT='https://github.com/ansible/django-ansible-base@'
export REGEX_RIGHT='#egg=django-ansible-base'

# GLOBALS
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REQ_FILE=$SCRIPT_DIR/requirements_git.txt

# Pin Function
DESIRED_VERSION=''
Pin()
{
    export DESIRED_VERSION
    perl -p -i -e 's/\Q$ENV{REGEX_LEFT}\E(.*?)\Q$ENV{REGEX_RIGHT}\E/$ENV{REGEX_LEFT}$ENV{DESIRED_VERSION}$ENV{REGEX_RIGHT}/g' $REQ_FILE
}

# Current Function
Current()
{
    REQUIREMENTS_LINE=$(grep django-ansible-base $REQ_FILE)

    echo "$REQUIREMENTS_LINE" | perl -nE 'say $1 if /\Q$ENV{REGEX_LEFT}\E(.*?)\Q$ENV{REGEX_RIGHT}\E/'
}


Help()
{
   # Display Help
   echo ""
   echo "Help:"
   echo ""
   echo "Interact with django-ansible-base in $REQ_FILE."
   echo "By default, output the current django-ansible-base pinned version."
   echo
   echo "Syntax: scriptTemplate [-s|h|v]"
   echo "options:"
   echo "s     Set django-ansible-base version to pin to."
   echo "h     Print this Help."
   echo "v     Verbose mode."
   echo
}

if [ $# -eq 0 ]; then
    Current
    exit
fi


while getopts ":hs:" option; do
   case $option in
      h) # display Help
         Help
         exit
         ;;
      s)
         DESIRED_VERSION=$OPTARG;;
      :)
         echo "Option -${OPTARG} requires an argument."
         Help
         exit 1
         ;;
     \?) # Invalid option
         echo "Error: Invalid option"
         echo ""
         Help
         exit;;
   esac
done

if [ -n "$DESIRED_VERSION" ]; then
    Pin
    Current
fi

