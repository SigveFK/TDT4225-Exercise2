--How many taxis, trips, and total GPS points are there?
SELECT
(SELECT COUNT(*) from taxis) AS taxi_count,
(SELECT COUNT(*) from trips) AS trip_count,
(SELECT COUNT(*) from trajectory_points) AS trajectory_point_count;

--What is the average number of trips per taxi?
--Denne kalkulerer kun blant taxiene som har minst én tur. Hvis du vil inkludere taxier uten turer, må du bruke en LEFT JOIN mellom taxis og trips.
SELECT AVG(trips_count)
FROM (
    SELECT taxi_id, COUNT(*) AS trips_count
    FROM trips
    GROUP BY taxi_id
) AS taxi_trips_counts
;

--List the top 20 taxis with the most trips.
SELECT taxi_id, COUNT(*) AS trips_count
FROM trips
GROUP BY taxi_id
ORDER BY trips_count DESC
LIMIT 20
;

--  What is the most used call type per taxi?
SELECT taxi_id, call_type, call_type_count
FROM (
    SELECT
        taxi_id,
        call_type,
        COUNT(*) AS call_type_count,
        RANK() OVER (
            PARTITION BY taxi_id
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM trips
    GROUP BY taxi_id, call_type
) x
WHERE rn = 1;

/*For each call type, compute the average trip duration and distance, and also
report the share of trips starting in four time bands: 00–06, 06–12, 12–18, and
18–24*/
SELECT
    call_type,
    AVG(duration) AS avg_duration,
    AVG(distance) AS avg_distance,

    SUM(CASE WHEN HOUR(start_time) >= 0  AND HOUR(start_time) < 6  THEN 1 ELSE 0 END) / COUNT(*) AS share_00_06,
    SUM(CASE WHEN HOUR(start_time) >= 6  AND HOUR(start_time) < 12 THEN 1 ELSE 0 END) / COUNT(*) AS share_06_12,
    SUM(CASE WHEN HOUR(start_time) >= 12 AND HOUR(start_time) < 18 THEN 1 ELSE 0 END) / COUNT(*) AS share_12_18,
    SUM(CASE WHEN HOUR(start_time) >= 18 AND HOUR(start_time) < 24 THEN 1 ELSE 0 END) / COUNT(*) AS share_18_24

FROM trips
GROUP BY call_type;

/*Find the taxis with the most total hours driven as well as total distance driven.
List them in order of total hours.*/
SELECT
    taxi_id,
    SUM(duration) / 3600 AS total_hours,
    SUM(distance) AS total_distance
FROM trips
GROUP BY taxi_id
ORDER BY total_hours DESC;


/* Find the trips that passed within 100 m of Porto City Hall.
(longitude, latitude) = (-8.62911, 41.15794) */
SELECT DISTINCT trip_id
FROM trajectory_points
WHERE ST_Distance_Sphere(
    POINT(longitude, latitude),
    POINT(-8.62911, 41.15794)
) <= 100;

/* Identify the number of invalid trips. An invalid trip is defined as a trip with fewer
than 3 GPS points.*/
SELECT COUNT(*) AS invalid_trips
FROM trips
WHERE point_count < 3;

/* Find the trips that started on one calendar day and ended on the next (midnight
crossers).*/
SELECT *
FROM trips
WHERE DATE(end_time) = DATE(start_time) + INTERVAL 1 DAY;

/* Find the trips whose start and end points are within 50 m of each other (circular
trips).*/
SELECT trip_id
FROM trips
WHERE end_longitude IS NOT NULL
  AND end_latitude IS NOT NULL
  AND ST_Distance_Sphere(
      POINT(start_longitude, start_latitude),
      POINT(end_longitude, end_latitude)
  ) <= 50;


/* For each taxi, compute the average idle time between consecutive trips. List the
top 20 taxis with the highest average idle time. */
SELECT
    taxi_id,
    AVG(TIMESTAMPDIFF(SECOND, previous_end, start_time)) / 3600 AS avg_idle_hours
FROM (
    SELECT
        taxi_id,
        start_time,
        LAG(end_time) OVER (
            PARTITION BY taxi_id
            ORDER BY start_time
        ) AS previous_end
    FROM trips
) AS t
WHERE previous_end IS NOT NULL
GROUP BY taxi_id
ORDER BY avg_idle_hours DESC
LIMIT 20;
