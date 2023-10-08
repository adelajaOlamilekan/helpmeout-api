#!/usr/bin/env bash
MEDIA_DIR="media"
DB="helpmeout.db"

if [ -d $MEDIA_DIR ]; then
    echo "Removing media directory"
    rm -rf $MEDIA_DIR
fi

if [ -f $DB ]; then
    echo "Removing database"
    rm $DB
fi
