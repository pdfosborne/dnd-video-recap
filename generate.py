import os
import base64
from openai import OpenAI
from moviepy import *
#from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def read_party_prompt():
    """Read the party prompt file"""
    try:
        with open("party_prompt.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Warning: party_prompt.txt not found. Proceeding without party prompt.")
        return ""

def get_segment_range(num_segments):
    """Get user input for which segments to process"""
    print(f"\nThere are {num_segments} segments available.")
    while True:
        choice = input("Enter segment number (e.g., '1'), range (e.g., '1-5'), or 'ALL': ").strip().upper()
        
        if choice == 'ALL':
            return list(range(1, num_segments + 1))
        
        try:
            if '-' in choice:
                start, end = map(int, choice.split('-'))
                if 1 <= start <= end <= num_segments:
                    return list(range(start, end + 1))
            else:
                segment = int(choice)
                if 1 <= segment <= num_segments:
                    return [segment]
        except ValueError:
            pass
        
        print(f"Invalid input. Please enter a number between 1 and {num_segments}, a range (e.g., '1-5'), or 'ALL'.")

def generate_image(prompt, output_path):
    """Generate an image using GPT Image API"""
    print(f"Generating image for: {prompt}")
    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt
        )
        
        # Decode base64 image data
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)
        
        # Save the image
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        
        print(f"Image saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return False

def create_final_video(base_name, segments_to_process):
    """Create a single video combining all segments"""
    print("Creating final video combining all segments...")
    try:
        # Create a list to store all video clips
        video_clips = []
        
        # Target resolution (16:9 aspect ratio - 720p)
        target_width = 1280
        target_height = 720
        
        # Process each selected segment
        for segment_num in segments_to_process:
            image_path = f"images/{base_name}/segment_{segment_num}.png"
            audio_path = f"segments/{base_name}/segment_{segment_num}.mp3"
            
            # Load and resize the image using PIL
            with Image.open(image_path) as img:
                # Resize while maintaining aspect ratio
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                # Create a temporary file for the resized image
                temp_path = f"images/{base_name}/temp_segment_{segment_num}.png"
                img.save(temp_path)
            
            # Load the resized image as a clip
            image_clip = ImageClip(temp_path)
            
            # Load the audio
            audio_clip = AudioFileClip(audio_path)
            
            # Set the duration of the image clip to match the audio
            image_clip = image_clip.with_duration(audio_clip.duration)
            
            # Set FPS for the image clip
            image_clip = image_clip.with_fps(24)
            
            # Add the audio to the image clip
            image_clip = image_clip.with_audio(audio_clip)
            
            # Combine the image and audio
            video_clip = CompositeVideoClip([image_clip])
            video_clips.append(video_clip)
            
            # Clean up the temporary file
            os.remove(temp_path)
        
        # Concatenate all video clips
        final_video = concatenate_videoclips(video_clips, method="compose", bg_color=None, padding=0)
        
        # Write the final video file
        output_path = f"videos/{base_name}/final_video.mp4"
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            threads=4,  # Use multiple threads for faster processing
            preset='medium',  # Encoding preset for better quality
            bitrate='5000k'  # Higher bitrate for better quality
        )
        
        print(f"Final video saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error creating final video: {str(e)}")
        return False

def get_highest_segment_number(base_name):
    """Get the highest segment number from transcript files"""
    transcripts_dir = f"transcripts/{base_name}"
    if not os.path.exists(transcripts_dir):
        return 0
    
    highest_num = 0
    for filename in os.listdir(transcripts_dir):
        if filename.startswith("segment_") and filename.endswith(".txt"):
            try:
                num = int(filename.split("_")[1].split(".")[0])
                highest_num = max(highest_num, num)
            except (ValueError, IndexError):
                continue
    return highest_num

def get_highest_audio_segment(base_name):
    """Get the highest audio segment number"""
    segments_dir = f"segments/{base_name}"
    if not os.path.exists(segments_dir):
        return 0
    
    highest_num = 0
    for filename in os.listdir(segments_dir):
        if filename.startswith("segment_") and filename.endswith(".mp3"):
            try:
                num = int(filename.split("_")[1].split(".")[0])
                highest_num = max(highest_num, num)
            except (ValueError, IndexError):
                continue
    return highest_num

def process_segments_for_images(base_name):
    """Process selected segments to generate images and create videos"""
    images_dir = f"images/{base_name}"
    videos_dir = f"videos/{base_name}"
    segments_dir = f"segments/{base_name}"
    transcripts_dir = f"transcripts/{base_name}"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    
    # Get the highest segment numbers for both transcripts and audio
    num_transcripts = get_highest_segment_number(base_name)
    num_audio = get_highest_audio_segment(base_name)
    
    if num_transcripts == 0:
        print(f"No transcript files found in {transcripts_dir}")
        return
    
    if num_audio == 0:
        print(f"No audio files found in {segments_dir}")
        return
    
    # Use the minimum of both to ensure we have both transcript and audio
    num_segments = min(num_transcripts, num_audio)
    if num_segments == 0:
        print("No matching segments found between transcripts and audio")
        return
    
    # Read the party prompt
    party_prompt = read_party_prompt()
    
    # Get which segments to process
    segments_to_process = get_segment_range(num_segments)
    
    # First generate all images
    for segment_num in segments_to_process:
        # Read the transcript file
        transcript_path = f"{transcripts_dir}/segment_{segment_num}.txt"
        try:
            with open(transcript_path, 'r') as f:
                transcript = f.read().strip()
        except FileNotFoundError:
            print(f"Transcript file not found: {transcript_path}")
            continue
        
        # Create a prompt for the image generation
        prompt = f"{party_prompt}\n\nCreate an image based on this transcript segment: {transcript}"
        
        # Generate and save the image
        image_path = f"{images_dir}/segment_{segment_num}.png"
        generate_image(prompt, image_path)
    
    # After all images are generated, create the final video using the selected segments
    create_final_video(base_name, segments_to_process) 