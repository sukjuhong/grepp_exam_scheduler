#!/bin/bash

pip install -r requirements.txt

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."

    cat <<EOL > "$ENV_FILE"
DEBUG=True
SECRET_KEY="+95BenWFBR+NXnzlaPSo50XDXhMhFQt15SdRjiULonutBv1kGjxBxBzPe/b42uPIWSxPzfxu5nb2aszqQxBxQw=="
DATABASE_URL=psql://postgres:postgres@localhost:5432/examscheduler

DJANGO_SUPERUSER_PASSWORD=grepp123
EOL
    echo ".env file created."
else
    echo ".env file already exists."
fi

python manage.py migrate
python manage.py createsuperuser --noinput --company_name=grepp
