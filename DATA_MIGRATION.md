# Migrating Data Between AWX Installations

## Introduction

Early versions of AWX did not support seamless upgrades between major versions and required the use of a backup and restore tool to perform upgrades.

As of version 18.0, `awx-operator` is the preferred install/upgrade method. Users who wish to upgrade modern AWX installations should follow the instructions at:

https://github.com/ansible/awx-operator/blob/devel/docs/upgrade/upgrading.md
