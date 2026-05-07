#!/bin/zsh

source config.sh

# Determine which architecture(s) to target when building the app bundle.
PY2APP_ARCH=${PY2APP_ARCH:-universal2}
case "$PY2APP_ARCH" in
    universal2)
        export ARCHFLAGS="-arch arm64 -arch x86_64"
        ;;
    arm64|x86_64)
        export ARCHFLAGS="-arch $PY2APP_ARCH"
        ;;
    *)
        echo "Unsupported PY2APP_ARCH value: $PY2APP_ARCH"
        echo "Use one of: arm64, x86_64, universal2."
        exit 1
        ;;
esac
echo "Building macos-deepseek-overlay for architecture: $PY2APP_ARCH"

# Create a build environment
touch temp.egg-info
rm -rf env dist build *.egg-info
python3 -m venv env
source env/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install setuptools==70.3.0 py2app pyobjc
build_dir_name=${0:a:h:t}
# Build the '.app' with 'py2app'
pushd ..
touch temp.egg-info
rm -rf dist build *.egg-info
python setup_deepseek.py py2app --arch "$PY2APP_ARCH" --dist-dir="$build_dir_name"/dist --bdist-base="$build_dir_name"/build
popd
# Deactivate the python building environment
deactivate

# Codesign all the '.so' files within the app
find dist/$APP_NAME.app -type f -name "*.so" -exec codesign --deep --force --verify --verbose --options runtime --timestamp --sign "$SIGNATURE" {} \;
# Codesign all the '.dylib' files within the app
find dist/$APP_NAME.app -type f -name "*.dylib" -exec codesign --deep --force --verify --verbose --options runtime --timestamp --sign "$SIGNATURE" {} \;
# Codesign the app itself
codesign --deep --force --verify --verbose --options runtime --timestamp --sign "$SIGNATURE" dist/$APP_NAME.app
# Create a ZIP for notary submission
ditto -c -k --keepParent dist/$APP_NAME.app $APP_NAME.zip
# Submit for notarization
xcrun notarytool submit $APP_NAME.zip --keychain-profile "$KEYCHAIN_PROFILE" --wait

# Check permissions to make sure it's valid
spctl -a -vvv -t exec dist/$APP_NAME.app
# Staple the permissions to the .app
xcrun stapler staple dist/$APP_NAME.app
# Create a DMG that provides an easy-installer
create-dmg --volname "$APP_NAME" --window-size 600 300 --icon-size 100 --app-drop-link 400 150 $APP_NAME.dmg dist/$APP_NAME.app