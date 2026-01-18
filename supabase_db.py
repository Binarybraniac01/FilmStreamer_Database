from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Supabase credentials from .env file
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = None


def init_database():
    """
    Initialize the Supabase client.
    Returns the Supabase client.
    """
    global supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"Supabase client initialized: {SUPABASE_URL}")
    return supabase


def insert_movie(client, title, link):
    """
    Insert a movie record into the Supabase database.
    Skips if the link already exists (to avoid duplicates).
    Returns True if inserted, False if already exists.
    """
    try:
        # Check if link already exists
        existing = client.table("movies").select("id").eq("link", link).execute()
        
        if existing.data and len(existing.data) > 0:
            # Link already exists, skip
            return False
        
        # Insert new record
        client.table("movies").insert({
            "title": title,
            "link": link
        }).execute()
        return True
        
    except Exception as e:
        print(f"Error inserting movie: {e}")
        return False


def get_all_movies(client):
    """
    Retrieve all movies from the Supabase database.
    """
    try:
        response = client.table("movies").select("id, title, link").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching movies: {e}")
        return []


def get_movie_count(client):
    """
    Get the total count of movies in the database.
    """
    try:
        response = client.table("movies").select("id", count="exact").execute()
        return response.count
    except Exception as e:
        print(f"Error getting count: {e}")
        return 0


def close_database(client):
    """
    Close the database connection (no-op for Supabase, but kept for compatibility).
    """
    print("Supabase session closed.")
