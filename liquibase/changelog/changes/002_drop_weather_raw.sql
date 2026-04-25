--liquibase formatted sql

--changeset sburdiug:002_drop_weather_raw dbms:postgresql runInTransaction:true
--preconditions onFail:HALT onError:HALT
--precondition-table-exists table:weather_record
--precondition-table-exists table:astronomy_info
--precondition-table-exists table:weather_raw

DROP TABLE weather_raw;
