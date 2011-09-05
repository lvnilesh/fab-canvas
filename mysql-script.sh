#!/bin/sh
# This is a comment
mysql -t --user=root --password=THIS-IS-A-VERY-SECURE-PASSWORD <<STOP
-- This is a comment inside an sql-command-stream.
create database canvas_production;
create database canvas_queue_production;
create user 'canvas'@'localhost' identified by 'THIS-IS-A-VERY-SECURE-PASSWORD';
grant all privileges on canvas_production.* to 'canvas'@'localhost' with grant option;
grant all privileges on canvas_queue_production.* to 'canvas'@'localhost' with grant option;
\q
STOP
test $? = 0 && echo "Your mysql batch job completed gracefully"