# Bincom Test - Delta State election results (Django REST Framework)

A small REST API (viewsets + mixins) on top of `bincom_test.sql`, with three pages that call it.

| Page | URL | API behind it |
|---|---|---|
| Q1 Polling unit result | `/polling-unit/` | `GET /api/lgas/`, `/api/wards/?lga=&with_units=1`, `/api/polling-units/?lga=&ward=`, `/api/polling-units/<id>/` |
| Q2 LGA summed total | `/lga-total/` | `GET /api/lgas/<lga_id>/total/` (computed from `announced_pu_results`, **not** `announced_lga_results`) |
| Q3 Add results | `/new-result/` | `GET /api/parties/`, `GET /api/wards/?lga=`, `POST /api/polling-units/` |

`/api/` also gives the browsable API, handy 

## Code layout

- `results/models.py`: unmanaged models mapped onto the existing tables (no migrations needed)
- `results/serializers.py`: list / detail / create serializers (create saves the polling unit and all party scores in one transaction)
- `results/views.py`: `ReadOnlyModelViewSet` for LGAs and wards; `ListModelMixin` for parties; `Create + List + Retrieve` mixins for polling units (no update/delete exposed)
- `results/services.py`: small shared helpers; `results/templates/`: the three pages

## Setup (Ubuntu)

1. Create the database and import the dump:

       sudo mysql -e "CREATE DATABASE bincomphptest;"
       sudo mysql bincomphptest < bincom_test.sql

   If the import complains about `0000-00-00` dates (MySQL 8 strict mode):

       sudo mysql --init-command="SET SESSION sql_mode=''" bincomphptest < bincom_test.sql

2. Create a database user and set the connection details:

       sudo mysql -e "CREATE USER 'bincom'@'localhost' IDENTIFIED BY 'bincom'; GRANT ALL ON bincomphptest.* TO 'bincom'@'localhost';"
       export DB_USER=bincom DB_PASSWORD=bincom      # optional: DB_NAME, DB_HOST, DB_PORT

3. Install and run:

       
       ppipenv install
       python manage.py runserver

   Open http://127.0.0.1:8000/

## Notes about the data

- `announced_pu_results.polling_unit_uniqueid` matches `polling_unit.uniqueid` (not `polling_unit_id`).
- `polling_unit.lga_id` matches `lga.lga_id` (not `lga.uniqueid`); `polling_unit.uniquewardid` matches `ward.uniqueid`.
- 170 of the 272 polling units are blank placeholder rows (hidden from the API); only 18 have results.
- `party_abbreviation` is CHAR(4), so LABOUR is stored as `LABO`; the API maps it back to LABOUR.
- Delta State = state id 25.
