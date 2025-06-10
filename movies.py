import customtkinter as ctk
import requests
import threading
from tkinter import messagebox
from PIL import Image
from io import BytesIO
import textwrap

class MovieRecommenderApp:
    def __init__(self, parent_frame):
        self.tmdb_api_key = ""
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.poster_base_url = "https://image.tmdb.org/t/p/w500"
        
        # Define moods with their corresponding emojis and descriptions
        self.moods = {
            "happy": {
                "emoji": "😊",
                "color": "#2dd4bf",  # Bright teal
                "description": "Cheerful & Light"
            },
            "sad": {
                "emoji": "😢",
                "color": "#4f46e5",  # Deep indigo
                "description": "Comfort Movies"
            },
            "excited": {
                "emoji": "🎉",
                "color": "#f43f5e",  # Vibrant rose
                "description": "High Energy"
            },
            "romantic": {
                "emoji": "❤️",
                "color": "#ec4899",  # Rich pink
                "description": "Love Stories"
            },
            "relaxed": {
                "emoji": "😌",
                "color": "#14b8a6",  # Calming teal
                "description": "Peaceful Viewing"
            },
            "scared": {
                "emoji": "😱",
                "color": "#7c3aed",  # Deep violet
                "description": "Thrillers"
            },
            "motivated": {
                "emoji": "💪",
                "color": "#f97316",  # Bright orange
                "description": "Feel Strong"
            },
            "adventurous": {
                "emoji": "🌟",
                "color": "#059669",  # Deep emerald
                "description": "Epic Stories"
            }
        }
        
        # Create main container
        self.main_container = ctk.CTkFrame(parent_frame)
        self.main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Left panel for mood selection
        self.left_panel = ctk.CTkFrame(self.main_container, width=300)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        # Title label in left panel
        self.title_label = ctk.CTkLabel(
            self.left_panel,
            text="How are you\nfeeling today?",
            font=("Helvetica", 20, "bold"),
            justify="center"
        )
        self.title_label.pack(pady=20)
        
        # Create mood buttons
        self.create_mood_buttons()
        
        # Right panel for recommendations
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Selected mood label
        self.selected_mood_label = ctk.CTkLabel(
            self.right_panel,
            text="Select a mood to see recommendations",
            font=("Helvetica", 16)
        )
        self.selected_mood_label.pack(pady=10)
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(
            self.right_panel,
            text="",
            font=("Helvetica", 12)
        )
        self.loading_label.pack()
        
        # Movie cards container
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.right_panel,
            width=800,
            height=600
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store references to movie cards and images
        self.movie_cards = []
        self.poster_images = []  # Keep references to avoid garbage collection

    def create_mood_buttons(self):
        for mood, info in self.moods.items():
            button = ctk.CTkButton(
                self.left_panel,
                text=f"{info['emoji']}\n{info['description']}",
                width=250,
                height=50,
                fg_color=info['color'],
                command=lambda m=mood: self.select_mood(m)
            )
            button.pack(pady=5, padx=10)

    




    #get mood selected
    def select_mood(self, mood):
        # Update mood label
        self.selected_mood_label.configure(
            text=f"Selected mood: {self.moods[mood]['emoji']} {self.moods[mood]['description']}"
        )
        # Clear existing cards before getting new recommendations
        self.clear_movie_cards()
        # Get new recommendations
        self.get_recommendations(mood)

    def create_movie_card(self, movie_data):
        try:
            card_frame = ctk.CTkFrame(self.scrollable_frame)
            card_frame.pack(pady=10, padx=10, fill="x")
            
            # Load and display movie poster
            if movie_data.get('poster_path'):
                poster_url = f"{self.poster_base_url}{movie_data['poster_path']}"
                response = requests.get(poster_url)
                image = Image.open(BytesIO(response.content))
                
                # Keep reference to the CTkImage
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(150, 225))
                self.poster_images.append(ctk_image)  # Store reference
                
                poster_label = ctk.CTkLabel(card_frame, image=ctk_image, text="")
                poster_label.image = ctk_image  # Keep reference
                poster_label.pack(side="left", padx=10, pady=10)
            
            # Movie details
            details_frame = ctk.CTkFrame(card_frame)
            details_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            # Title
            title_label = ctk.CTkLabel(
                details_frame,
                text=movie_data['title'],
                font=("Helvetica", 16, "bold")
            )
            title_label.pack(anchor="w")
            
            # Release date
            if movie_data.get('release_date'):
                release_label = ctk.CTkLabel(
                    details_frame,
                    text=f"Release Date: {movie_data['release_date']}"
                )
                release_label.pack(anchor="w")
            
            # Rating
            if movie_data.get('vote_average'):
                rating_label = ctk.CTkLabel(
                    details_frame,
                    text=f"Rating: {movie_data['vote_average']}/10"
                )
                rating_label.pack(anchor="w")
            
            # Overview
            if movie_data.get('overview'):
                overview = textwrap.fill(movie_data['overview'], width=60)
                overview_label = ctk.CTkLabel(
                    details_frame,
                    text=overview,
                    wraplength=600,
                    justify="left"
                )
                overview_label.pack(anchor="w")
            
            return card_frame
            
        except Exception as e:
            print(f"Error creating movie card: {e}")
            if 'card_frame' in locals():
                card_frame.destroy()
            return None

    def clear_movie_cards(self):
        # Properly destroy all movie cards and clear references
        for card in self.movie_cards:
            for widget in card.winfo_children():
                widget.destroy()
            card.destroy()
        self.movie_cards.clear()
        self.poster_images.clear()  # Clear image references

    def process_recommendations(self, mood):
        try:
            response = self.send_to_deepseek(mood)
            content = response['choices'][0]['message']['content']
            movies = [movie.strip() for movie in content.split('#') if movie.strip()]
            
            for movie_name in movies[:10]:  # Limit to 10 movies
                movie_data = self.search_movie_tmdb(movie_name)
                if movie_data:
                    card = self.create_movie_card(movie_data)
                    if card:
                        self.movie_cards.append(card)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Update UI in the main thread
            self.main_container.after(0, lambda: self.loading_label.configure(text=""))

    def get_recommendations(self, mood):
        self.loading_label.configure(text=f"Getting recommendations for {mood} mood...")
        thread = threading.Thread(target=lambda: self.process_recommendations(mood))
        thread.daemon = True
        thread.start()

    def search_movie_tmdb(self, movie_name):
        try:
            search_url = f"{self.tmdb_base_url}/search/movie"
            params = {
                "api_key": self.tmdb_api_key,
                "query": movie_name,
                "language": "en-US"
            }
            response = requests.get(search_url, params=params)
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                return data['results'][0]
            return None
            
        except Exception as e:
            print(f"Error searching TMDB: {e}")
            return None

    def send_to_deepseek(self, mood):
        url = "https://api.hyperbolic.xyz/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ3YXlhc3l0QGdtYWlsLmNvbSIsImlhdCI6MTczNTY3MDQyNX0.uTQe4LHUoyTIligLGiJSU1I0C5lGfJG4mlXtc0vAFWc"
        }
        
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                        Recommended movies to improve mood.
                        mood: {mood}
                        Show only movie names, separated by #.
                    """
                }
            ],
            "model": "deepseek-ai/DeepSeek-V3",
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
