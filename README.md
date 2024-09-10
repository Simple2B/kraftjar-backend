# kraftjar-be

Flask Portal, Fast API backend, DB for Kraftjar App

1. Run

```bash
poetry install
```

2. Create '.env' file (simply copy file .env.sample):

3. Run

```bash
docker compose up d db
```

to create an docker container

4. Development and debugging

   This project contains both Flask and FastAPI.

   To run Flask app:

   - go to "Run and Debug" tab in VSCode and select "Python:Flask" from dropdown menu

   To run FastAPI app:

   - go to "Run and Debug" tab in VSCode and select "API" from dropdown menu

   After selection, press `"Run and Debug"` button or `F5` key on keyboard

5. Create db with command

```bash
flask db upgrade
```

6. In main folder need install node_modules to work with tailwind, run

```bash
yarn
```

## Commands to get data into your local db:

Go to `ssh s2b` and take the backup file from our server and put it in your environment:

```bash
cp /home/runner/kraftjar/backup/db_2024-09-10T12:56:35Z.tgz .
```

```bash
mv db_2024-09-10T12:56:35Z.tgz dump.tgz
```

In our project, download dump.tgz:

```bash
scp s2b:dump.tgz .
```

```bash
tar xvzf dump.tgz
```

Clear db and fill with data:

```bash
dcdn -v db
```

```bash
dcupd db
```

```bash
dce -T db psql < dump.sql
```
