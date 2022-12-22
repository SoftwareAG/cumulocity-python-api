# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

NAME="$1"
VERSION="$2"
IMG_NAME=`echo "$NAME" | tr '[:upper:]' '[:lower:]' | tr '[:punct:]' '-'`
BUILD_DIR="./build/samples/$NAME"
DIST_DIR="./dist/samples/$NAME"
TARGET="$DIST_DIR/$IMG_NAME.zip"

echo "Name: $NAME, Image Name: $IMG_NAME, Version: $VERSION"
echo "Build directory: $BUILD_DIR"
echo "Dist directory:  $DIST_DIR"
echo "Target location: $TARGET"
echo ""

if ! [[ -d "samples" ]]; then
  echo "This script must be run from the project base directory."
  exit 2
fi

if ! [[ -f "./samples/$NAME.py" ]]; then
  echo "Unable to find sample source file."
  exit 2
fi

# prepare directories
[[ -d "$BUILD_DIR" ]] && rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
[[ -d "$DIST_DIR" ]] && rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# copy & render sources
cp ./requirements.txt "$BUILD_DIR"
cp "./samples/$NAME.py" "$BUILD_DIR"
cp -r "./c8y_api" "$BUILD_DIR"
sed -e "s/{VERSION}/$VERSION/g" ./samples/cumulocity.json > "$BUILD_DIR/cumulocity.json"
sed -e "s/{SAMPLE}/$NAME/g" ./samples/Dockerfile > "$BUILD_DIR/Dockerfile"
# extend cumulocity.json is defined
if [[ -r ./samples/cumulocity-$NAME.json ]]; then
  echo -n "Found custom extension at './samples/cumulocity-$NAME.json'. Applying ..."
  tmp=`tempfile`
  jq -s '.[0] + .[1]' "$BUILD_DIR/cumulocity.json" ./samples/cumulocity-$NAME.json > $tmp
  mv $tmp "$BUILD_DIR/cumulocity.json"
  echo "  Done."
fi

# build image
echo "Building image ..."
docker build -t "$NAME" "$BUILD_DIR"
docker save -o "$DIST_DIR/image.tar" "$NAME"
zip -j "$DIST_DIR/$IMG_NAME.zip" "$BUILD_DIR/cumulocity.json" "$DIST_DIR/image.tar"

echo ""
echo "Created uploadable archive: $TARGET"