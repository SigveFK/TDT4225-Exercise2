CREATE TABLE IF NOT EXISTS taxis (
    taxi_id INT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id BIGINT PRIMARY KEY,
    taxi_id INT NOT NULL,
    call_type ENUM('A', 'B', 'C') NOT NULL,
    origin_call INT NULL,
    origin_stand INT NULL,
    day_type ENUM('A', 'B', 'C') NOT NULL,
    missing_data BOOLEAN NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    duration INT NULL,
    point_count INT NOT NULL,
    distance DOUBLE NULL,
    start_longitude DOUBLE NULL,
    start_latitude DOUBLE NULL,
    end_longitude DOUBLE NULL,
    end_latitude DOUBLE NULL,
    CONSTRAINT fk_trip_taxi
        FOREIGN KEY (taxi_id) REFERENCES taxis (taxi_id)
        ON DELETE CASCADE,
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