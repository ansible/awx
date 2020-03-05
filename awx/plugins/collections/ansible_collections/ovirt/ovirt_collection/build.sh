#!/bin/bash

VERSION="1.0.0"
MILESTONE=master
RPM_RELEASE="0.1.$MILESTONE.$(date -u +%Y%m%d%H%M%S)"

COLLECTION_NAME="ovirt_collection"
COLLECTION_NAMESPACE="ovirt"

PACKAGE_NAME="ovirt-ansible-collection"
PREFIX=/usr/local
DATAROOT_DIR=$PREFIX/share
COLLECTIONS_DATAROOT_DIR=$DATAROOT_DIR/ansible/collections/ansible_collections
DOC_DIR=$DATAROOT_DIR/doc
PKG_DATA_DIR=${PKG_DATA_DIR:-$COLLECTIONS_DATAROOT_DIR/$COLLECTION_NAMESPACE/$COLLECTION_NAME}
PKG_DATA_DIR_ORIG=${PKG_DATA_DIR_ORIG:-$PKG_DATA_DIR}
PKG_DOC_DIR=${PKG_DOC_DIR:-$DOC_DIR/$PACKAGE_NAME}

RPM_VERSION=$VERSION
PACKAGE_VERSION=$VERSION
[ -n "$MILESTONE" ] && PACKAGE_VERSION+="_$MILESTONE"
DISPLAY_VERSION=$PACKAGE$VERSION

TARBALL="$PACKAGE_NAME-$PACKAGE_VERSION.tar.gz"

dist() {
  echo "Creating tar archive '$TARBALL' ... "
  sed \
   -e "s|@RPM_VERSION@|$RPM_VERSION|g" \
   -e "s|@RPM_RELEASE@|$RPM_RELEASE|g" \
   -e "s|@PACKAGE_NAME@|$PACKAGE_NAME|g" \
   -e "s|@PACKAGE_VERSION@|$PACKAGE_VERSION|g" \
   < ovirt-ansible-collection.spec.in > ovirt-ansible-collection.spec

  git ls-files | tar --files-from /proc/self/fd/0 -czf "$TARBALL" ovirt-ansible-collection.spec
  echo "tar archive '$TARBALL' created."
}

install() {
  echo "Installing data..."
  mkdir -p $PKG_DATA_DIR
  mkdir -p $PKG_DOC_DIR

  cp -pR plugins/ $PKG_DATA_DIR

  echo "Installation done."
}

$1
