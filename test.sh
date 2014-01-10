#!/bin/sh

TEST_FOLDER=/tmp/pocheToCalibreTest

ebook-convert pocheToCalibre.recipe .epub --test -vv --debug-pipeline debug --username pocheToCalibre --password pocheToCalibre

rm -rf $TEST_FOLDER
mkdir $TEST_FOLDER
unzip pocheToCalibre.epub -d $TEST_FOLDER > /dev/null

rm $TEST_FOLDER/content.opf $TEST_FOLDER/toc.ncx

diff -r $TEST_FOLDER testTarget

if [ $? -eq 0 ]
then
    echo "Test OK"
fi
