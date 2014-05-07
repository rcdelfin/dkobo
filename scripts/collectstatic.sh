#!/bin/sh
python manage.py collectstatic --noinput --settings=dkobo.settings
grunt build_all
python manage.py compress --settings=dkobo.settings
python manage.py collectstatic --noinput --settings=dkobo.settings
python manage.py run_gunicorn --settings=dkobo.settings -b 0.0.0.0:$PORT