# Restoring a saved SQL

- Create the save from Python Anywhere
- Copy the SQL file `backups/` folder as `backups/db-backup.sql`
- Log into the MySQL container:
  - `sudo docker exec tymenu_mysql bash -c "cd /backups;./docker_import_db.sh db-backup.sql"`
