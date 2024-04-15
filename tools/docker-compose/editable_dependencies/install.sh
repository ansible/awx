for file in `ls /editable_dependencies`; do
    echo "Installing $file"
    pip install -e /editable_dependencies/$file
done
