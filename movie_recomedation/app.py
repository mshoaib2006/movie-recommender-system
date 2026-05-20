import streamlit as st
import pandas as pd
import pickle
import requests
import mysql.connector
from mysql.connector import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

st.set_page_config(
    page_title="Movie Recommender System",
    layout="wide"
)


DB_CONFIG = {
    "host": "localhost",
    "user": "movieflix_user",
    "password": "Movieflix@123",
    "database": "movie_recommender"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def signup_user(full_name, email, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users(full_name, email, password)
            VALUES(%s, %s, %s)
        """, (full_name, email, hashed_password))

        conn.commit()
        cursor.close()
        conn.close()

        return True, "Account created successfully"

    except IntegrityError:
        return False, "Email already exists. Please login."

    except Exception as e:
        return False, str(e)


def login_user(email, password):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            return True, user

        return False, None

    except Exception as e:
        st.error(f"Login error: {e}")
        return False, None


def save_selected_movie(user_id, movie_name):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_selected_movies(user_id, movie_name)
            VALUES(%s, %s)
        """, (user_id, movie_name))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Selected movie save error: {e}")


def save_recommended_movie(user_id, selected_movie, recommended_movie, similarity_score):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_recommended_movies(
                user_id,
                selected_movie,
                recommended_movie,
                similarity_score
            )
            VALUES(%s, %s, %s, %s)
        """, (
            user_id,
            selected_movie,
            recommended_movie,
            float(similarity_score)
        ))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Recommended movie save error: {e}")


def get_selected_history(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT movie_name, created_at
            FROM user_selected_movies
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))

        history = cursor.fetchall()

        cursor.close()
        conn.close()

        return history

    except Exception as e:
        st.error(f"History error: {e}")
        return []


def get_recommendation_history(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT selected_movie, recommended_movie, similarity_score, created_at
            FROM user_recommended_movies
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))

        history = cursor.fetchall()

        cursor.close()
        conn.close()

        return history

    except Exception as e:
        st.error(f"Recommendation history error: {e}")
        return []


@st.cache_data
def load_movie_data():
    movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
    movies_df = pd.DataFrame(movies_dict)

    similarity_data = pickle.load(open("similarity.pkl", "rb"))

    return movies_df, similarity_data



def fetch_poster(movie_id):
    try:
        api_key = ""
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

        response = requests.get(url, timeout=10)
        data = response.json()

        poster_path = data.get("poster_path")

        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path

        return None

    except Exception:
        return None


def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    recommended_scores = []

    for i in movies_list:
        movie_row_index = i[0]
        score = i[1]

        movie_id = movies.iloc[movie_row_index].movie_id
        movie_title = movies.iloc[movie_row_index].title

        recommended_movies.append(movie_title)
        recommended_movies_posters.append(fetch_poster(movie_id))
        recommended_scores.append(round(float(score) * 100, 2))

    return recommended_movies, recommended_movies_posters, recommended_scores



try:
    movies, similarity = load_movie_data()
except Exception as e:
    st.error(f"Movie files loading error: {e}")
    st.stop()


if "user" not in st.session_state:
    st.session_state.user = None


st.sidebar.title(" Movie Recommender")

if st.session_state.user:
    st.sidebar.success(f"Logged in as {st.session_state.user['full_name']}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

menu = st.sidebar.radio(
    "Menu",
    ["Signup", "Login", "Movie Recommender", "My History"]
)


if menu == "Signup":
    st.title("Create Account")
    st.write("Create your account to save your movie recommendations.")

    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Signup"):
        if not full_name or not email or not password:
            st.error("All fields are required")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            success, message = signup_user(full_name, email, password)

            if success:
                st.success(message)
                st.info("Now go to Login page and login.")
            else:
                st.error(message)



elif menu == "Login":
    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.error("Email and password are required")
        else:
            success, user = login_user(email, password)

            if success:
                st.session_state.user = user
                st.success(f"Welcome {user['full_name']}")
                st.rerun()
            else:
                st.error("Invalid email or password")


elif menu == "Movie Recommender":
    if st.session_state.user is None:
        st.warning("Please login first.")
        st.stop()

    st.title("Movie Recommender System")

    selected_movie_name = st.selectbox(
        "Select a movie",
        movies["title"].values
    )

    if st.button("Show Recommendation"):
        save_selected_movie(
            st.session_state.user["user_id"],
            selected_movie_name
        )

        names, posters, scores = recommend(selected_movie_name)

        st.subheader("Recommended Movies")

        col1, col2, col3, col4, col5 = st.columns(5)
        columns = [col1, col2, col3, col4, col5]

        for index, col in enumerate(columns):
            with col:
                st.text(names[index])

                if posters[index]:
                    st.image(posters[index])
                else:
                    st.warning("No poster found")

                st.caption(f"Similarity: {scores[index]}%")

                save_recommended_movie(
                    st.session_state.user["user_id"],
                    selected_movie_name,
                    names[index],
                    scores[index]
                )

        st.success("Selected movie and recommended movies saved in MySQL.")


elif menu == "My History":
    if st.session_state.user is None:
        st.warning("Please login first.")
        st.stop()

    st.title("My History")

    st.subheader("Selected Movies")
    selected_history = get_selected_history(st.session_state.user["user_id"])

    if selected_history:
        for item in selected_history:
            st.write(f"✔ {item['movie_name']} — {item['created_at']}")
    else:
        st.info("No selected movies found.")

    st.divider()

    st.subheader("Recommended Movies History")
    rec_history = get_recommendation_history(st.session_state.user["user_id"])

    if rec_history:
        for item in rec_history:
            st.write(
                f"🎬 Selected: {item['selected_movie']} → "
                f"Recommended: {item['recommended_movie']} "
                f"({item['similarity_score']}%) — {item['created_at']}"
            )
    else:
        st.info("No recommended movies found.")
