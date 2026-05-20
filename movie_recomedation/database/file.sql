CREATE DATABASE IF NOT EXISTS movie_recommender;
USE movie_recommender;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_selected_movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    movie_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_recommended_movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    selected_movie VARCHAR(255) NOT NULL,
    recommended_movie VARCHAR(255) NOT NULL,
    similarity_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE USER IF NOT EXISTS 'movieflix_user'@'localhost' IDENTIFIED BY 'Movieflix@123';

GRANT ALL PRIVILEGES ON movie_recommender.* TO 'movieflix_user'@'localhost';

FLUSH PRIVILEGES;

USE movie_recommender;

SELECT * FROM users;

SELECT * FROM user_selected_movies;

SELECT * FROM user_recommended_movies;

USE movie_recommender;

CREATE OR REPLACE VIEW full_user_movie_history AS
SELECT
    u.user_id,
    u.full_name,
    u.email,
    us.movie_name AS selected_movie,
    urm.recommended_movie,
    urm.similarity_score,
    us.created_at AS selected_movie_time,
    urm.created_at AS recommendation_time
FROM users u
LEFT JOIN user_selected_movies us
    ON u.user_id = us.user_id
LEFT JOIN user_recommended_movies urm
    ON u.user_id = urm.user_id
    AND us.movie_name = urm.selected_movie;
    
    SELECT * FROM full_user_movie_history;