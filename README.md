## How to start?
```
git clone https://github.com/c-sachdeva/kheltambola.git
cd tambola
python manage.py migrate
python manage.py runserver
```

## How to set up sql?
Refer to Install and Configure MySQL paragraph in EC2-Django-Guide.pdf
```
mysql
create database django character set utf8;
quit;
```
If you need to delete all the data in your MySQL database, delete and remigrate with:
```
mysql
drop database django;
create database django character set utf8;
quit;
```
Delete migrations folder, then
```
python manage.py makemigrations tambola
python manage.py migrate
python manage.py runserver
```
