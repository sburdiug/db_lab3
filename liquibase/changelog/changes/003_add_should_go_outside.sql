--liquibase formatted sql

--changeset sburdiug:003_add_should_go_outside dbms:postgresql runInTransaction:true
--preconditions onFail:HALT onError:HALT
--precondition-table-exists table:weather_record
--precondition-table-exists table:astronomy_info

ALTER TABLE weather_record
    ADD COLUMN IF NOT EXISTS should_go_outside BOOLEAN;

UPDATE weather_record wr
SET should_go_outside =
CASE
    WHEN ai.sunrise IS NOT NULL
     AND ai.sunset IS NOT NULL
     AND ai.moonrise IS NOT NULL
     AND ai.moonset IS NOT NULL
     AND ai.sunset > ai.sunrise
     AND ai.moon_illumination >= 35
     AND LOWER(ai.moon_phase) NOT LIKE '%new moon%'
     AND ai.moonrise <= TIME '22:00:00'
     AND (
        (
            EXTRACT(MONTH FROM wr.last_updated) BETWEEN 4 AND 10
            AND wr.temperature_celsius BETWEEN 8 AND 30
            AND wr.wind_kph <= 30
        )
        OR
        (
            EXTRACT(MONTH FROM wr.last_updated) NOT BETWEEN 4 AND 10
            AND wr.temperature_celsius BETWEEN 0 AND 18
            AND wr.wind_kph <= 20
        )
     )
    THEN TRUE
    ELSE FALSE
END
FROM astronomy_info ai
WHERE ai.weather_record_id = wr.id;

UPDATE weather_record
SET should_go_outside = FALSE
WHERE should_go_outside IS NULL;

ALTER TABLE weather_record
    ALTER COLUMN should_go_outside SET NOT NULL;

--rollback ALTER TABLE weather_record DROP COLUMN IF EXISTS should_go_outside;
