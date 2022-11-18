
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

# build image

docker build -t "$NAME" "$BUILD_DIR"
docker save -o "$DIST_DIR/image.tar" "$NAME"
zip -j "$DIST_DIR/$IMG_NAME.zip" "$BUILD_DIR/cumulocity.json" "$DIST_DIR/image.tar"

echo ""
echo "Created uploadable archive: $TARGET"