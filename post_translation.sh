#!/bin/bash

# Rename the zh_cn folder 
mv translations/zh_cn translations/zh

# Create a directory for core (locale)
# rm -rf locale
mkdir locale

# Copy all subdirectories to locale
cp -r translations/ locale/

# Loop over each directory and create another directory LC_Messages
# Move django.po files to LC_Messages and remove messages.po
cd locale/
for d in */ ; do
    dir=${d%*/}
    mkdir $dir/LC_MESSAGES
    mv $dir/django.po $dir/LC_MESSAGES/
    rm $dir/messages.po
done

cd ..
# echo $(pwd)

# Create a directory for ui (locales)
# rm -rf locales
mkdir locales

# Copy all subdirectories to locales
cp -r translations/ locales/

# Loop over each directory and remove django.po
cd locales
for d in */ ; do
    dir=${d%*/}
    rm $dir/django.po
done

cd .. 

# echo $pwd

# cd to repository

# cd _clones/

awx_core_path="awx/" # locale will be dropped here
awx_ui_path="awx/ui/src/" # locales will be dropped here

rsync -av locale/ $awx_core_path
rsync -av locales/ $awx_ui_path

rm -rf translations/
