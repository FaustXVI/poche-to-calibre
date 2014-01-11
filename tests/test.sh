#!/bin/sh

TEST_FOLDER=/tmp/pocheToCalibreTest
FILE_TARGET=pocheToCalibre.epub
RECIPE=pocheToCalibre.recipe

cp ../pocheToCalibre.py $RECIPE

rm -rf $FILE_TARGET $TEST_FOLDER

ebook-convert $RECIPE $FILE_TARGET --test -vv --debug-pipeline debug --username pocheToCalibre --password pocheToCalibre &&

mkdir -p $TEST_FOLDER &&
unzip $FILE_TARGET -d $TEST_FOLDER > /dev/null &&
rm $TEST_FOLDER/content.opf $TEST_FOLDER/toc.ncx &&
diff -r $TEST_FOLDER testTarget

if [ $? -eq 0 ]
then
    echo "Test OK"
fi
