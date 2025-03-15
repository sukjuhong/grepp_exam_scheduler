#!/bin/bash

pip install -r requirements.txt

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."

    cat <<EOL > "$ENV_FILE"
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG
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
python manage.py shell -c "
from customers.models import Customer;

try:
    customer = Customer.objects.create(company_name='programmers')
    customer.set_password('programmers123')
    customer.save()
except:
    print('programmers customer already exists')

try:
    customer = Customer.objects.create(company_name='monito')
    customer.set_password('monito123')
    customer.save()
except:
    print('monito customer already exists')
"
