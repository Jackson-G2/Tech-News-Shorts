import requests
import json
from datetime import datetime, timedelta
import openai
from dotenv import load_dotenv, find_dotenv
import os
import re  # Add at the top with other imports
import time
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, CompositeAudioClip
import wave
import contextlib
from moviepy.config import change_settings
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
from PIL import Image, ImageFilter
from PIL.Image import Resampling
import moviepy.video.fx.all as vfx
import numpy as np

# Configure paths
FFMPEG_BINARY = r"C:\Users\jimmy\Desktop\Programming\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
IMAGEMAGICK_BINARY = os.path.join("C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI", "magick.exe")

# Configure MoviePy settings
change_settings({
    "IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY,
    "FFMPEG_BINARY": FFMPEG_BINARY
})

# Set environment variable for pydub
os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_BINARY)

# Get the current directory and find .env file
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')

print("\nChecking .env file...")
print(f"Found .env file at: {env_path}")

# Try to read and parse the .env file directly
try:
    with open(env_path, 'r') as f:
        env_content = f.read().strip()  # Remove any trailing whitespace
        print("Successfully read .env file")
        
        # Parse the content manually to ensure proper formatting
        env_vars = {}
        for line in env_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # Set the environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        # Get the API key
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print("OPENAI_API_KEY is set (length:", len(api_key), "characters)")
            # Create OpenAI client with the key
            client = openai.OpenAI(api_key=api_key)
            print("OpenAI client created successfully")
        else:
            print("OPENAI_API_KEY is NOT set!")
            print("Please check your .env file format. It should be:")
            print("OPENAI_API_KEY=your_key_here")
            print("(no quotes, no spaces around the equals sign)")
            print("\nCurrent .env content:")
            print(env_content)
            exit(1)
            
except Exception as e:
    print(f"Error reading .env file: {e}")
    exit(1)

# News API configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY', "3eaf85f028e44181bf14ed2025b587b5")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Keywords configuration
TECH_AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "deep learning", "neural networks",
    "computer vision", "NLP", "large language models", "transformers", "OpenAI", "ChatGPT",
    "Llama", "DeepMind", "AGI", "ASI", "generative AI", "autonomous systems", "automation",
    "robotics", "humanoid robots", "Boston Dynamics", "AI research", "reinforcement learning",
    "AI ethics", "superintelligence", "AI safety", "singularity", "AI alignment",
    "prompt engineering", "diffusion models", "multimodal AI", "synthetic data",
    "AI regulation", "federated learning", "AI inference", "AI chips", "neuromorphic computing",
    "cognitive computing", "deep reinforcement learning", "evolutionary algorithms", "GANs",
    "diffusion models", "multi-agent systems", "AI bias", "self-supervised learning",
    "autoencoders", "adversarial AI", "AI-generated content", "digital humans",
    "hyperautomation", "embodied AI", "robotics process automation", "RPA"
]

SCIENCE_SPACE_KEYWORDS = [
    "NASA", "space exploration", "SpaceX", "Blue Origin", "rocket science", "astrophysics",
    "cosmology", "exoplanets", "black holes", "dark matter", "quantum mechanics", "CERN",
    "Higgs boson", "LHC", "antimatter", "gravitational waves", "fusion energy", "ITER",
    "nuclear fusion", "superconductors", "graphene", "nanotechnology", "bioengineering",
    "synthetic biology", "genetic engineering", "CRISPR", "DNA sequencing", "longevity research",
    "anti-aging", "neuroscience", "brain-machine interfaces", "neurotech", "BCI", "Neuralink",
    "mind uploading", "consciousness studies", "astrobiology", "habitable exoplanets", "JWST",
    "Hubble", "Artemis program", "lunar gateway", "Mars colonization", "interstellar travel",
    "Alcubierre drive", "Dyson sphere", "Kardashev scale", "wormholes", "dark energy",
    "neutrinos", "quantum entanglement", "qubit", "cryogenics", "superconducting magnets",
    "terraforming", "orbital mechanics", "asteroid mining", "space debris removal",
    "planetary defense", "photonics", "optical computing", "RNA sequencing", "gene editing",
    "epigenetics", "proteomics", "bioinformatics", "AI in medicine", "bioelectricity",
    "organoids", "lab-grown organs", "neuroprosthetics", "cybernetic implants",
    "mind-machine interface"
]

COMPUTING_CYBERSECURITY_KEYWORDS = [
    "supercomputers", "quantum computing", "quantum supremacy", "IBM Q", "Google Sycamore",
    "cybersecurity", "ethical hacking", "penetration testing", "encryption", "cryptography",
    "blockchain", "decentralized networks", "Web3", "cybersecurity threats", "zero-day exploits",
    "data privacy", "digital forensics", "homomorphic encryption", "post-quantum cryptography",
    "zero-trust security", "SIEM", "SOAR", "threat intelligence", "cyber warfare",
    "AI-driven cyber attacks", "ransomware", "malware", "APT", "advanced persistent threats",
    "red teaming", "SOC", "security operations center", "ethical AI", "federated learning security",
    "data anonymization", "deepfake detection", "adversarial networks", "phishing",
    "identity theft", "credential stuffing", "hardware security modules", "HSM", "botnet detection",
    "edge security", "cloud security", "cryptographic accelerators", "trusted execution environments",
    "TEE"
]

FUTURISM_TECH_KEYWORDS = [
    "futurism", "transhumanism", "bionics", "exoskeletons", "nanorobots", "biotechnology",
    "biohacking", "metaverse", "AR", "VR", "MR", "brain-computer interface", "digital twins",
    "holography", "smart cities", "self-driving cars", "autonomous vehicles", "Tesla", "Waymo",
    "EVs", "solid-state batteries", "graphene batteries", "wireless power", "IoT", "Industry 4.0",
    "cyber-physical systems", "edge computing", "digital transformation", "brain uploading",
    "consciousness transfer", "digital immortality", "xenobots", "synthetic embryos",
    "bioengineered organs", "carbon capture", "direct air capture", "geoengineering",
    "AI-augmented creativity", "quantum internet", "photonic processors", "6G networks",
    "swarm robotics", "drone swarms", "AI in warfare", "DNA storage", "3D bioprinting",
    "self-assembling materials", "shape-memory alloys", "plasma propulsion", "autonomous drones",
    "AI-driven drug discovery", "lab-on-a-chip", "self-replicating machines", "smart materials",
    "hyperloop", "AI-powered nanomedicine", "lunar mining", "asteroid belt colonization",
    "post-humanism"
]

EXCLUDE_KEYWORDS = [
    "gaming", "esports", "video games", "PlayStation", "Xbox", "Nintendo", "entertainment",
    "Hollywood", "movies", "celebrity", "Netflix", "Disney", "music", "sports", "football",
    "basketball", "politics", "election", "Biden", "Trump", "war", "conflict", "scandal",
    "gossip", "TikTok", "Kardashian", "YouTube drama", "reality TV", "Marvel", "DC", "Bollywood",
    "hip hop", "rap", "K-pop", "Oscars", "Grammys", "TikTok trends", "YouTube controversy",
    "celebrity gossip", "royal family", "pop culture", "fashion", "TV shows", "sitcom",
    "romance", "viral trends", "cooking shows", "reality competition", "stand-up comedy",
    "gossip blogs", "social media influencers"
]

def build_query():
    """
    Build the query string for the News API.
    This function creates a search query that looks for breakthrough and innovative news.
    """
    # Define keywords that indicate breakthrough or innovative content
    keywords = [
        "breakthrough", "discovery", "revolutionary", "innovative", "groundbreaking",
        "first-ever", "milestone", "achievement", "advancement", "cutting-edge",
        "pioneering", "novel", "unprecedented", "world-first"
    ]
    
    # Join all keywords with OR operator and wrap each in quotes
    # This means the API will look for articles containing ANY of these words
    query = " OR ".join(f'"{kw}"' for kw in keywords)
    return query

def fetch_news():
    """
    Fetch news articles from the News API.
    This function handles the API request and returns the news data.
    """
    # Get the search query
    query = build_query()
    
    # Calculate date range (last 2 days up to now)
    date_from = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    # Define trusted sources for tech and science news
    sources = [
        "nature", "science", "scientific-american", "new-scientist", "technologyreview",
        "wired", "ars-technica", "techcrunch"
    ]
    
    # Prepare the API request parameters
    params = {
        'q': query,                    # The search query
        'from': date_from,             # Start date
        'to': date_to,                 # End date
        'sources': ','.join(sources),  # Comma-separated list of sources
        'sortBy': 'relevancy',         # Sort results by relevance
        'language': 'en',              # English language only
        'pageSize': 100,               # Maximum number of results
        'apiKey': NEWS_API_KEY         # Your API key
    }
    
    try:
        # Print debug information about the request
        print(f"Making API request with query: {query}")
        print(f"Date range: from {date_from} to {date_to}")
        print(f"Sources: {sources}")
        
        # Make the API request
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        # Print response information
        print(f"API Response status: {response.status_code}")
        print(f"Total results: {data.get('totalResults', 0)}")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return None

def score_article(article):
    """
    Score an article based on various factors to determine its quality.
    Returns a score between 0 and 100.
    """
    score = 0
    
    # Source reputation scoring - Adjusted for tech focus
    source_scores = {
        "techcrunch": 100,  # Highest priority for tech news
        "wired": 95,        # Strong tech focus
        "ars-technica": 95, # Strong tech focus
        "technologyreview": 90,
        "nature": 75,
        "science": 75,
        "scientific-american": 70,
        "new-scientist": 70
    }
    
    # Add source score
    source_name = article['source']['name'].lower()
    score += source_scores.get(source_name, 50)  # Default score of 50 for unknown sources
    
    # Score based on content length
    content_length = len(article.get('description', '') or '') + len(article.get('content', '') or '')
    if content_length > 1000:
        score += 20
    elif content_length > 500:
        score += 10
    
    # Score based on keyword density in title and description
    tech_keywords = [
        "AI", "artificial intelligence", "machine learning", "deep learning", "neural networks",
        "computer vision", "NLP", "large language models", "transformers", "OpenAI", "ChatGPT",
        "Llama", "DeepMind", "AGI", "ASI", "generative AI", "autonomous systems", "automation",
        "robotics", "humanoid robots", "Boston Dynamics", "AI research", "reinforcement learning",
        "AI ethics", "superintelligence", "AI safety", "singularity", "AI alignment",
        "prompt engineering", "diffusion models", "multimodal AI", "synthetic data",
        "AI regulation", "federated learning", "AI inference", "AI chips", "neuromorphic computing"
    ]
    
    breakthrough_keywords = [
        "breakthrough", "discovery", "revolutionary", "innovative", "groundbreaking",
        "first-ever", "milestone", "achievement", "advancement", "cutting-edge"
    ]
    
    # Combine all keywords
    all_keywords = tech_keywords + breakthrough_keywords
    
    # Score the text
    text = f"{article['title']} {article.get('description', '')}".lower()
    
    # Give higher weight to tech keywords
    tech_matches = sum(2 for keyword in tech_keywords if keyword.lower() in text)
    breakthrough_matches = sum(1 for keyword in breakthrough_keywords if keyword.lower() in text)
    
    score += tech_matches + breakthrough_matches
    
    return score

def get_top_articles(articles, count=3):
    """
    Get the top N articles based on scoring.
    """
    # Score each article
    scored_articles = [(article, score_article(article)) for article in articles]
    
    # Sort by score in descending order
    scored_articles.sort(key=lambda x: x[1], reverse=True)
    
    # Return only the top N articles
    return [article for article, score in scored_articles[:count]]

def clean_title(title):
    """
    Remove source names and other unwanted prefixes from titles using regex.
    """
    # List of sources to remove from titles
    sources_to_remove = [
        "TechCrunch", "Wired", "Ars Technica", "Nature", "Science",
        "Scientific American", "New Scientist", "Technology Review"
    ]
    
    # Create a regex pattern for all sources
    pattern = r'\s*[|—–-…]\s*(' + '|'.join(sources_to_remove) + r')\s*$'
    
    # Remove source names using regex
    title = re.sub(pattern, '', title)
    
    # Additional cleanup for any remaining source mentions
    for source in sources_to_remove:
        title = title.replace(source, '')
    
    # Clean up any remaining separators
    title = re.sub(r'\s*[|—–-…]\s*$', '', title)
    
    return title.strip()

def display_news(news_data):
    """
    Display the news articles in a readable format.
    This function prints the articles to the console in a structured way.
    """
    # Check if we have valid data and articles
    if not news_data or not news_data.get('articles'):
        print("No articles found.")
        return
    
    # Get the top 3 articles
    top_articles = get_top_articles(news_data['articles'])
    
    # Print each article's title and description
    for article in top_articles:
        # Clean the title before displaying
        clean_title_text = clean_title(article['title'])
        print(f"{clean_title_text}")
        if article.get('description'):
            print(f"{article['description']}")
        print()  # Empty line between articles

def process_with_openai(articles):
    """
    Process articles through OpenAI to create a 1-minute news segment.
    """
    # Use the global client
    global client
    
    # Take only the top 3 articles
    top_articles = articles[:3]
    
    # Format the articles for the prompt, ensuring titles are cleaned
    articles_text = ""
    for i, article in enumerate(top_articles, 1):
        # Clean the title before using it
        clean_title_text = clean_title(article['title'])
        articles_text += f"Article {i}:\n"
        articles_text += f"Headline: {clean_title_text}\n"
        articles_text += f"Summary: {article['description']}\n\n"
    
    prompt = f"""You are a writer creating a 1-minute spoken news segment from three brief tech news articles. Each article includes a short headline and a summary. Your job is to:

1. Rewrite each headline to sound more engaging and click-worthy, like a YouTube or podcast title.
2. Summarize each story in a clear, concise way that is optimized for a text-to-speech model.
3. Ensure the total combined output is around 800–1000 characters (including spaces), suitable for a 1-minute read time.
4. Fix any incomplete or cut-off sentences so the summaries sound natural and complete.
5. Keep the tone energetic and conversational, as if you're reading the news aloud.
6. Do NOT include any numbering or bullet points in the output.

Here are the articles:

{articles_text}

Now generate the rewritten segment."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional news writer specializing in creating engaging, spoken news segments."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Return the complete rewritten segment
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error processing articles with OpenAI: {e}")
        return None

def save_to_file(news_data, filename="tech_news.json"):
    """
    Save the news data to a JSON file.
    This function persists the news data for later use.
    """
    try:
        # Get top 3 articles before saving
        if news_data and news_data.get('articles'):
            news_data['articles'] = get_top_articles(news_data['articles'])
        
        # Open file in write mode and save the JSON data
        with open(filename, 'w') as f:
            json.dump(news_data, f, indent=2)  # indent=2 makes the JSON file readable
        print(f"Top 3 news articles saved to {filename}")
    except IOError as e:
        print(f"Error saving to file: {e}")

def analyze_tts_timing(text):
    """
    Analyze the text to create precise timing for each word/phrase.
    Returns a list of tuples (text, start_time, duration) for each subtitle segment.
    """
    # Split text into words and analyze punctuation
    words = text.split()
    segments = []
    current_time = 0
    
    # Process words in small groups (1-3 words)
    i = 0
    while i < len(words):
        # Determine segment size (1-3 words)
        segment_size = min(3, len(words) - i)
        
        # Check if we should break at punctuation
        if i + segment_size < len(words):
            next_word = words[i + segment_size]
            if any(p in next_word for p in ['.', '!', '?', ',', ';', ':']):
                segment_size = min(segment_size, 2)  # Prefer shorter segments before punctuation
        
        # Create segment
        segment = ' '.join(words[i:i + segment_size])
        
        # Calculate duration based on:
        # - Base time per word (0.35s for alloy voice)
        # - Extra time for punctuation
        # - Extra time for sentence endings
        duration = len(segment.split()) * 0.35
        
        # Add time for punctuation
        if any(p in segment for p in [',', ';', ':']):
            duration += 0.2
        if any(p in segment for p in ['.', '!', '?']):
            duration += 0.5
        
        segments.append((segment, current_time, duration))
        current_time += duration
        i += segment_size
    
    return segments

def process_text_for_tts(text):
    """
    Process the text for TTS and create precise subtitle timing.
    """
    # Split into lines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    processed_lines = []
    subtitle_segments = []
    
    current_time = 0
    
    # Process each line
    for line in lines:
        # Skip headlines and numbers
        if line.startswith(('Headline:', '1.', '2.', '3.')):
            continue
            
        # Skip empty lines
        if not line.strip():
            continue
            
        # Handle transitions between stories
        if line.strip().startswith('Summary:'):
            processed_lines.append("Next up,")
            subtitle_segments.append(("Next up,", current_time, 1))
            current_time += 1
            line = line.replace('Summary:', '').strip()
        
        # Analyze timing for this line
        line_segments = analyze_tts_timing(line)
        
        # Adjust timing to start from current_time
        for segment, _, duration in line_segments:
            processed_lines.append(segment)
            subtitle_segments.append((segment, current_time, duration))
            current_time += duration
    
    # Add outro
    processed_lines.append("That's all for today's tech news update.")
    subtitle_segments.append(("That's all for today's tech news update.", current_time, 3))
    
    # Join all lines with spaces for the final TTS text
    processed_text = ' '.join(processed_lines)
    return processed_text, subtitle_segments

def resize_video(clip, width=None, height=None):
    """
    Resize a video clip while maintaining aspect ratio.
    Uses the newer PIL Resampling constants.
    """
    w, h = clip.size
    if width is None and height is None:
        return clip
    elif width is None:
        width = int(w * height / h)
    elif height is None:
        height = int(h * width / w)
    
    try:
        def resize_frame(frame):
            img = Image.fromarray(frame)
            try:
                # Try the newer Resampling.LANCZOS first
                resized = img.resize((width, height), Resampling.LANCZOS)
            except (AttributeError, TypeError):
                try:
                    # Fallback to older Image.LANCZOS
                    resized = img.resize((width, height), Image.LANCZOS)
                except (AttributeError, TypeError):
                    # Last resort: use BICUBIC
                    resized = img.resize((width, height), Image.BICUBIC)
            return np.array(resized)
        
        return clip.fl_image(resize_frame)
    except Exception as e:
        print(f"Error in resize_video: {e}")
        # Return original clip if resize fails
        return clip

def get_pexels_videos(query, count=5):
    """
    Fetch multiple relevant videos from Pexels based on the query.
    Returns a list of paths to downloaded videos.
    """
    try:
        # Get Pexels API key from environment
        api_key = os.getenv('PEXELS_API_KEY')
        if not api_key:
            print("PEXELS_API_KEY not found in environment variables")
            return None
        
        # Search for videos
        print(f"Searching Pexels for videos matching: {query}")
        headers = {"Authorization": api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page={count}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('videos'):
            print(f"No videos found for query: {query}")
            return None
        
        video_paths = []
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download each video
        for i, video in enumerate(data['videos']):
            try:
                # Get the smallest file size that's still HD quality
                video_files = sorted(
                    [v for v in video['video_files'] if v['quality'] in ['hd', 'sd']],
                    key=lambda x: x['width'] * x['height']
                )
                if not video_files:
                    continue
                    
                video_url = video_files[0]['link']
                print(f"Downloading video {i+1}/{count} for {query}...")
                video_response = requests.get(video_url, stream=True)
                video_response.raise_for_status()
                
                video_path = os.path.join(temp_dir, f"pexels_{query.replace(' ', '_')}_{i}.mp4")
                with open(video_path, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                video_paths.append(video_path)
                
            except Exception as e:
                print(f"Error downloading video {i+1}: {e}")
                continue
        
        if video_paths:
            print(f"Successfully downloaded {len(video_paths)} videos for query: {query}")
            return video_paths
        else:
            print(f"No suitable videos found for query: {query}")
            return None
        
    except Exception as e:
        print(f"Error fetching Pexels videos: {e}")
        return None

def extract_keywords_from_segment(text, start_time, end_time):
    """
    Extract more specific and relevant keywords from a text segment.
    Returns the most relevant keywords for that segment.
    """
    try:
        # Remove only the most common words to preserve context
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after',
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'can', 'could', 'may', 'might', 'must', 'shall',
            'this', 'that', 'these', 'those', 'it', 'its', 'it\'s',
            'i', 'you', 'he', 'she', 'we', 'they',
            'my', 'your', 'his', 'her', 'our', 'their',
            'am', 'is', 'are', 'was', 'were'
        }
        
        # Split into words and clean up
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out only the most common words
        keywords = [word for word in words if word not in common_words]
        
        # If no keywords found, use some general tech-related terms
        if not keywords:
            return ['technology innovation research']
        
        # Get the most frequent and relevant keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        
        # Sort by frequency and length (prefer longer words)
        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: (x[1], len(x[0])),
            reverse=True
        )
        
        # Take top 4-5 keywords
        top_keywords = [word for word, count in sorted_keywords[:5]]
        
        # Create more specific search queries with context
        queries = []
        
        # Add the full phrase as first query
        queries.append(' '.join(top_keywords))
        
        # Add combinations that preserve context
        if len(top_keywords) >= 3:
            queries.append(' '.join(top_keywords[:3]))  # First 3 words
            queries.append(' '.join(top_keywords[1:4]))  # Middle 3 words
            queries.append(' '.join(top_keywords[-3:]))  # Last 3 words
        
        # Add individual significant words
        for word in top_keywords:
            if len(word) > 4:  # Only add longer words
                queries.append(word)
        
        return queries
        
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return ['technology innovation']  # Default fallback

def create_pip_video_sequence(subtitle_segments, target_width, target_height, total_duration):
    """
    Create a sequence of PIP videos based on subtitle segments.
    Returns a list of video clips with their positions and timings.
    """
    pip_clips = []
    current_time = 0
    segment_duration = 3.0  # Duration for each video segment
    temp_files = []  # Keep track of temporary files
    
    # Calculate PIP box dimensions
    box_width = int(target_width * 0.8)  # 80% of screen width
    box_height = int(target_height * 0.4)  # 40% of screen height
    
    # Add padding to the box
    padding = 20
    box_x = (target_width - box_width - padding*2) // 2
    box_y = padding  # Add padding at the top
    
    # Group subtitle segments by time windows
    time_windows = []
    current_window = []
    window_end = segment_duration
    
    for segment in subtitle_segments:
        if segment['start'] < window_end:
            current_window.append(segment)
        else:
            if current_window:
                time_windows.append(current_window)
            current_window = [segment]
            window_end = segment['start'] + segment_duration
    
    if current_window:
        time_windows.append(current_window)
    
    print(f"\nProcessing {len(time_windows)} video segments...")
    
    try:
        # Process each time window
        for i, window in enumerate(time_windows, 1):
            print(f"\nProcessing segment {i}/{len(time_windows)}")
            
            # Combine text from all segments in the window
            window_text = ' '.join(segment['text'] for segment in window)
            start_time = window[0]['start']
            
            # Extract keywords and get videos
            keyword_queries = extract_keywords_from_segment(window_text, start_time, start_time + segment_duration)
            print(f"Keywords extracted: {keyword_queries}")
            
            # Try each keyword combination until we find a suitable video
            video_paths = None
            for query in keyword_queries:
                video_paths = get_pexels_videos(query, count=1)
                if video_paths:
                    break
            
            if video_paths:
                temp_files.extend(video_paths)
                for video_path in video_paths:
                    try:
                        print(f"Processing video: {os.path.basename(video_path)}")
                        # Load video with optimized settings
                        video = VideoFileClip(video_path, audio=False)
                        
                        # Trim to segment duration if needed
                        if video.duration > segment_duration:
                            print("Trimming video to segment duration...")
                            video = video.subclip(0, segment_duration)
                        
                        # Pre-calculate the resize dimensions
                        resize_factor = box_width / video.w
                        new_height = int(video.h * resize_factor)
                        
                        try:
                            print("Resizing video...")
                            # Resize video efficiently with error handling
                            resized_video = resize_video(video, width=box_width, height=new_height)
                            
                            print("Positioning video...")
                            # Position the video with padding
                            positioned_video = (resized_video
                                             .set_position((box_x + padding, box_y + padding))
                                             .set_start(start_time)
                                             .set_duration(segment_duration))
                            
                            pip_clips.append(positioned_video)
                            print("Video segment processed successfully")
                            
                        except Exception as e:
                            print(f"Error processing video resize: {e}")
                            continue
                            
                    except Exception as e:
                        print(f"Error processing video {video_path}: {e}")
                        continue
                    finally:
                        if hasattr(video, 'close'):
                            video.close()
            else:
                print(f"No videos found for segment {i}, skipping...")
        
        print(f"\nSuccessfully processed {len(pip_clips)} video segments")
        return pip_clips, temp_files  # Return both clips and temp files
        
    except Exception as e:
        print(f"Error in create_pip_video_sequence: {e}")
        return [], temp_files  # Return empty clips but still return temp files for cleanup

def process_video_with_audio(audio_file, subtitle_segments, bg_video_path="bg/bg.mp4"):
    """
    Process the video with audio and subtitles.
    Returns the path to the output video file.
    """
    clips_to_close = []  # Keep track of clips to close
    temp_files = []  # Keep track of temporary files
    
    try:
        print("Loading background video...")
        # Load background video with optimized settings
        bg_video = VideoFileClip(bg_video_path, audio=False)  # Disable audio loading for bg video
        clips_to_close.append(bg_video)
        
        print("Loading audio...")
        # Load audio
        audio = AudioFileClip(audio_file)
        clips_to_close.append(audio)
        
        # Get the exact audio duration
        audio_duration = audio.duration
        print(f"Audio duration: {audio_duration:.2f} seconds")
        
        print("Loading background music...")
        # Load background music
        bg_music = AudioFileClip("bg/bg-sound-track-DFF.mp3")
        clips_to_close.append(bg_music)
        
        # Set background music volume to 10%
        bg_music = bg_music.volumex(0.1)
        
        # Loop background music if needed
        if bg_music.duration < audio_duration:
            bg_music = bg_music.loop(duration=audio_duration)
        
        # Trim background music to match audio duration
        bg_music = bg_music.subclip(0, audio_duration)
        
        # Combine main audio with background music
        final_audio = CompositeAudioClip([audio, bg_music])
        clips_to_close.append(final_audio)
        
        # Calculate dimensions for vertical format (9:16)
        target_width = 1080  # Standard vertical video width
        target_height = 1920  # Standard vertical video height
        
        # Create multiple background video segments for variety
        print("Creating background video segments...")
        bg_segments = []
        segment_duration = 10.0  # Change background every 10 seconds
        
        for start_time in range(0, int(audio_duration), int(segment_duration)):
            # Calculate resize factor to maintain aspect ratio and cover the height
            resize_factor = target_height / bg_video.h
            new_width = int(bg_video.w * resize_factor)
            
            # Use the optimized resize_video function
            video_segment = resize_video(bg_video, width=new_width, height=target_height)
            
            # Create video segment with the same duration as audio
            video_segment = video_segment.subclip(start_time % bg_video.duration, 
                                                (start_time + segment_duration) % bg_video.duration)
            
            # Crop to target width
            x_center = video_segment.w / 2
            video_segment = video_segment.crop(
                x1=x_center - target_width/2,
                x2=x_center + target_width/2,
                y1=0,
                y2=target_height
            )
            
            # Set the start time for this segment
            video_segment = video_segment.set_start(start_time)
            bg_segments.append(video_segment)
            clips_to_close.append(video_segment)
        
        print("Creating PIP video sequence...")
        # Create PIP video sequence with progress updates
        pip_clips, temp_files = create_pip_video_sequence(subtitle_segments, target_width, target_height, audio_duration)
        if pip_clips:
            clips_to_close.extend(pip_clips)
        
        print("Creating subtitle clips...")
        # Create subtitle clips with batched processing
        subtitle_clips = []
        total_segments = len(subtitle_segments)
        for i, segment in enumerate(subtitle_segments, 1):
            if i % 5 == 0:  # Show progress every 5 segments
                print(f"Processing subtitle {i}/{total_segments}")
            
            # Create text clip with improved settings for vertical format
            text_clip = TextClip(
                segment['text'],
                fontsize=48,
                color='white',
                font='Arial',
                stroke_color='black',
                stroke_width=0.5,
                size=(target_width * 0.9, None),
                method='caption',
                align='center'
            ).set_position(('center', target_height * 0.5))  # Move subtitles to middle of screen
            
            # Set timing
            text_clip = text_clip.set_start(segment['start']).set_duration(segment['end'] - segment['start'])
            clips_to_close.append(text_clip)
            
            # Create background with improved efficiency
            bg_clip = (ColorClip(size=(text_clip.w + 80, text_clip.h + 40), color=(0, 0, 0))
                      .set_opacity(0.3)
                      .set_position(('center', target_height * 0.5))  # Move subtitle background to middle
                      .set_start(segment['start'])
                      .set_duration(segment['end'] - segment['start']))
            clips_to_close.append(bg_clip)
            
            subtitle_clips.extend([bg_clip, text_clip])
        
        print("Combining all clips...")
        # Combine all clips with optimized settings
        final_video = CompositeVideoClip(
            bg_segments + pip_clips + subtitle_clips,
            size=(target_width, target_height)
        ).set_audio(final_audio)  # Use the combined audio with background music
        
        # Trim the final video to match the exact audio duration
        final_video = final_video.subclip(0, audio_duration)
        clips_to_close.append(final_video)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/final_video_{timestamp}.mp4"
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        print("Writing final video...")
        # Write the final video with optimized settings
        final_video.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=30,
            preset='ultrafast',  # Use ultrafast preset for maximum speed
            threads=8,  # Use maximum available threads
            bitrate='8000k',  # High bitrate for quality
            ffmpeg_params=[
                '-tune', 'film',  # Optimize for film-like content
                '-profile:v', 'high',  # Use high profile
                '-movflags', '+faststart',  # Enable fast start for web playback
                '-bf', '2',  # Use 2 B-frames
                '-g', '30',  # GOP size of 30
                '-crf', '23',  # Slightly higher CRF for faster encoding
                '-pix_fmt', 'yuv420p'  # Ensure compatibility
            ]
        )
        
        print(f"Video successfully saved to {output_file}")
        
        # Upload to YouTube if credentials are available
        try:
            upload_to_youtube(output_file)
        except Exception as e:
            print(f"Error uploading to YouTube: {e}")
        
        return output_file
        
    except Exception as e:
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        print("Cleaning up resources...")
        # Clean up all clips
        for clip in clips_to_close:
            try:
                if hasattr(clip, 'close'):
                    clip.close()
            except Exception as e:
                print(f"Error closing clip: {e}")
        
        # Clean up temporary files after video is written
        print("\nCleaning up temporary files...")
        import time
        time.sleep(0.5)  # Add a small delay before cleanup
        
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            os.remove(temp_file)
                            print(f"Removed: {temp_file}")
                            break
                        except PermissionError:
                            if attempt < 2:  # If not the last attempt
                                time.sleep(0.5)  # Wait before retry
                                continue
                            print(f"Could not remove {temp_file} after 3 attempts - file may be in use")
                        except Exception as e:
                            print(f"Error removing temp file {temp_file}: {e}")
                            break
            except Exception as e:
                print(f"Error accessing temporary file {temp_file}: {e}")

def upload_to_youtube(video_path):
    """
    Upload a video to YouTube using the YouTube Data API.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import pickle
        import os.path
        
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        creds = None
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Get video title from the news segment
        with open('news_segments/news_segment_*.txt', 'r') as f:
            title = f.read().split('\n')[0]  # Use first line as title
        
        # Prepare the video metadata
        body = {
            'snippet': {
                'title': title,
                'description': 'Daily tech news update',
                'tags': ['tech', 'news', 'update', 'AI', 'technology'],
                'categoryId': '28'  # Science & Technology category
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Upload the video
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        print("Uploading video to YouTube...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        print(f"Video uploaded successfully! Video ID: {response['id']}")
        return response['id']
        
    except Exception as e:
        print(f"Error uploading to YouTube: {e}")
        raise

def check_env():
    """
    Check for the presence of the .env file and required environment variables.
    """
    print("Checking .env file...")
    
    # Check if .env file exists
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        raise Exception("No .env file found. Please create one with your OPENAI_API_KEY.")
    
    print(f"Found .env file at: {env_path}")
    
    # Load environment variables from .env file
    load_dotenv(env_path)
    print("Successfully read .env file")
    
    # Check if OPENAI_API_KEY is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception("OPENAI_API_KEY not found in .env file")
    
    print(f"OPENAI_API_KEY is set (length: {len(api_key)} characters)")
    
    # Check if PEXELS_API_KEY is set
    pexels_key = os.getenv('PEXELS_API_KEY')
    if not pexels_key:
        print("Warning: PEXELS_API_KEY not found in .env file. Picture-in-picture videos will be disabled.")
    else:
        print("PEXELS_API_KEY is set")

def create_openai_client():
    """
    Create and return an OpenAI client using the API key from environment variables.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception("OPENAI_API_KEY not found in environment variables")
    
    client = openai.OpenAI(api_key=api_key)
    print("OpenAI client created successfully")
    return client

def generate_srt(text, output_file):
    """
    Generate an SRT subtitle file from the input text.
    """
    try:
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate timing
        duration_per_sentence = 3  # seconds
        current_time = 0
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, sentence in enumerate(sentences, 1):
                start_time = current_time
                end_time = start_time + duration_per_sentence
                
                # Format times as HH:MM:SS,mmm
                start_str = format_srt_time(start_time)
                end_str = format_srt_time(end_time)
                
                # Write SRT entry
                f.write(f"{i}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{sentence}\n\n")
                
                current_time = end_time
                
    except Exception as e:
        print(f"Error generating SRT file: {e}")

def format_srt_time(seconds):
    """
    Format time in seconds to SRT time format (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def create_subtitle_clips(subtitle_segments, video_size):
    """
    Create subtitle clips with precise timing and improved visibility.
    """
    subtitle_clips = []
    for text, start_time, duration in subtitle_segments:
        # Create text clip with improved settings
        txt_clip = TextClip(
            text,
            fontsize=48,
            color='white',
            stroke_color='black',
            stroke_width=2,
            font='Arial-Bold',
            size=(video_size[0] * 0.9, None),
            method='caption',
            align='center'
        )
        
        # Position in the center of the screen
        txt_clip = txt_clip.set_position(('center', 'center'))
        
        # Add semi-transparent background
        bg_clip = ColorClip(size=video_size, color=(0, 0, 0))
        bg_clip = bg_clip.set_opacity(0.3)
        bg_clip = bg_clip.set_duration(duration)
        bg_clip = bg_clip.set_start(start_time)
        
        # Combine background and text
        combined_clip = CompositeVideoClip([bg_clip, txt_clip])
        combined_clip = combined_clip.set_start(start_time).set_duration(duration)
        
        subtitle_clips.append(combined_clip)
    
    return subtitle_clips

def adjust_subtitle_timing(audio_duration, subtitle_segments):
    """
    Fine-tune subtitle timing to match the actual audio duration.
    """
    total_subtitle_time = sum(duration for _, _, duration in subtitle_segments)
    
    # Only adjust if the difference is significant
    if abs(total_subtitle_time - audio_duration) > 0.1:
        # Calculate adjustment factor
        scale_factor = audio_duration / total_subtitle_time
        
        # Apply adjustment while maintaining relative timing
        adjusted_segments = []
        current_time = 0
        
        for text, _, duration in subtitle_segments:
            adjusted_duration = duration * scale_factor
            adjusted_segments.append((text, current_time, adjusted_duration))
            current_time += adjusted_duration
        
        return adjusted_segments
    
    return subtitle_segments

def save_with_timestamp(content, prefix, extension):
    """
    Save content to a file with timestamp.
    """
    # Create folders if they don't exist
    os.makedirs("news_segments", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"news_segments/{prefix}_{timestamp}.{extension}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def text_to_speech(text, output_file):
    """
    Convert text to speech using OpenAI's TTS API.
    """
    try:
        # Create OpenAI client
        client = create_openai_client()
        
        # Create speech using OpenAI's TTS
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Save the audio file
        response.stream_to_file(output_file)
        print(f"Audio file saved as {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error converting text to speech: {e}")
        return None

def get_audio_duration(audio_file):
    """
    Get the duration of an audio file in seconds using moviepy.
    """
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    audio.close()
    return duration

def analyze_audio_file(audio_file):
    """
    Analyze the audio file to detect speech segments and create subtitle timings.
    Returns a list of subtitle segments with start and end times.
    """
    try:
        print("Analyzing audio file...")
        # Load audio file using pydub
        audio = AudioSegment.from_mp3(audio_file)
        audio_duration = len(audio) / 1000.0  # Convert to seconds
        print(f"Audio duration: {audio_duration:.2f} seconds")
        
        # Read the text file corresponding to the audio file
        text_file = audio_file.replace('.mp3', '.txt')
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        print(f"Found {len(sentences)} sentences to process")
        
        # Calculate total words and average words per second
        total_words = sum(len(sentence.split()) for sentence in sentences)
        words_per_second = total_words / audio_duration
        print(f"Average words per second: {words_per_second:.2f}")
        
        # Create subtitle segments
        subtitle_segments = []
        current_time = 0
        
        for sentence in sentences:
            words = sentence.split()
            if not words:
                continue
            
            # Calculate duration based on actual audio length
            segment_duration = len(words) / words_per_second
            end_time = min(current_time + segment_duration, audio_duration)
            
            # Split long sentences into smaller chunks if needed
            if len(words) > 8:
                print(f"Splitting long sentence ({len(words)} words) into chunks...")
                # Split into smaller chunks
                for i in range(0, len(words), 8):
                    chunk_words = words[i:i+8]
                    if not chunk_words:
                        continue
                    
                    chunk_duration = len(chunk_words) / words_per_second
                    chunk_end_time = min(current_time + chunk_duration, audio_duration)
                    
                    subtitle_segments.append({
                        'start': current_time,
                        'end': chunk_end_time,
                        'text': ' '.join(chunk_words)
                    })
                    current_time = chunk_end_time
            else:
                subtitle_segments.append({
                    'start': current_time,
                    'end': end_time,
                    'text': sentence
                })
                current_time = end_time
            
            # Add a small pause between sentences
            current_time = min(current_time + 0.1, audio_duration)
        
        print(f"Created {len(subtitle_segments)} subtitle segments")
        return subtitle_segments
        
    except Exception as e:
        print(f"Error analyzing audio file: {e}")
        import traceback
        traceback.print_exc()
        # Return empty segments if analysis fails
        return []

def main():
    """
    Main function to run the news content generation pipeline.
    """
    try:
        # Check for .env file and load environment variables
        check_env()
        
        # Create OpenAI client
        client = create_openai_client()
        
        # Fetch news articles
        news_data = fetch_news()
        if not news_data or 'articles' not in news_data:
            raise Exception("No articles found in the news data")
            
        articles = news_data['articles'][:3]  # Get top 3 articles
        
        # Generate news segment
        news_segment = process_with_openai(articles)
        
        # Save news segment to file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_file = f"news_segments/news_segment_{timestamp}.txt"
        srt_file = f"news_segments/news_segment_{timestamp}.srt"
        audio_file = f"news_segments/news_segment_{timestamp}.mp3"
        
        # Create directories if they don't exist
        os.makedirs("news_segments", exist_ok=True)
        
        # Save text content
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(news_segment)
        print(f"Processed text saved to {text_file}")
        
        # Generate SRT file
        generate_srt(news_segment, srt_file)
        print(f"Subtitles saved to {srt_file}")
        
        # Generate audio file
        text_to_speech(news_segment, audio_file)
        print(f"Audio saved to {audio_file}")
        
        # Analyze audio to get subtitle segments
        subtitle_segments = analyze_audio_file(audio_file)
        
        # Process video with audio and subtitles
        video_file = process_video_with_audio(audio_file, subtitle_segments)
        print(f"Final video saved to {video_file}")
        
        # Save top 3 articles to JSON
        save_to_file({'articles': articles})
        print("Top 3 news articles saved to tech_news.json")
        
    except Exception as e:
        print(f"Error in main function: {e}")

# This is the standard Python idiom for running the script directly
if __name__ == "__main__":
    main()