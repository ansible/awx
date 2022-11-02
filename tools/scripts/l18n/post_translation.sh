#!/bin/bash

# Rename the zh_cn folder 
mv translations/zh_cn translations/zh

# Create a directory for api (locale)
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

# Create a directory for ui (locales)
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

awx_api_path="awx/locale" # locale will be dropped here
awx_ui_path="awx/ui/src/locales" # locales will be dropped here

rsync -av locale/ $awx_api_path
rsync -av locales/ $awx_ui_path

rm -rf translations/
rm -rf locale/
rm -rf locales/

