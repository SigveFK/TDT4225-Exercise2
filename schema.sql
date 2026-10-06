CREATE TABLE IF NOT EXISTS trips (
    trip_id BIGINT PRIMARY KEY,
    taxi_id INT NOT NULL,
    day_type ENUM('A', 'B', 'C') NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration INT NOT NULL,
    point_count INT NOT NULL,
    distance DOUBLE NOT NULL,
    start_longitude DOUBLE NOT NULL,
    start_latitude DOUBLE NOT NULL,
    end_longitude DOUBLE NOT NULL,
    end_latitude DOUBLE NOT NULL,
    call_type ENUM('A', 'B', 'C') NOT NULL,
    missing_data BOOLEAN NOT NULL,
    origin_call INT NULL,
    origin_stand INT NULL,
    taxi_id INT NOT NULL,
    CONSTRAINT fk_trip_taxi
        FOREIGN KEY (taxi_id) REFERENCES taxis (taxi_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS taxis (
    taxi_id BIGINT PRIMARY KEY,
);

CREATE TABLE IF NOT EXISTS trajectory_points (
    trip_id BIGINT NOT NULL,
    point_index INT NOT NULL,
    longitude DOUBLE NOT NULL,
    latitude DOUBLE NOT NULL,
    PRIMARY KEY (trip_id, point_index),
    CONSTRAINT fk_trajectory_trip
        FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON DELETE CASCADE
);