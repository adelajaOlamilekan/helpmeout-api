#!/usr/bin/env bash
MEDIA_DIR="media"
DB="screen_recording_app.db"

if [ -d $MEDIA_DIR ]; then
    echo "Removing media directory"
    rm -rf media
fi

if [ -f $DB ]; then
    echo "Removing database"
    rm helpmeout.db
fi
