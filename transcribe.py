import os
from pydub import AudioSegment
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime
from generate import process_segments_for_images

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def check_existing_files(input_file):
    """Check if segments or transcripts already exist for the input file"""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    segments_dir = f"segments/{base_name}"
    transcript_file = f"transcripts/{base_name}.txt"
    images_dir = f"images/{base_name}"
    videos_dir = f"videos/{base_name}"
    
    existing_files = []
    if os.path.exists(segments_dir) and os.listdir(segments_dir):
        existing_files.append(f"Segments directory: {segments_dir}")
    if os.path.exists(transcript_file):
        existing_files.append(f"Transcript file: {transcript_file}")
    if os.path.exists(images_dir) and os.listdir(images_dir):
        existing_files.append(f"Images directory: {images_dir}")
    if os.path.exists(videos_dir) and os.listdir(videos_dir):
        existing_files.append(f"Videos directory: {videos_dir}")
    
    return existing_files

def get_user_confirmation(existing_files):
    """Prompt user for confirmation to proceed"""
    if not existing_files:
        return True
    
    print("\nThe following files already exist:")
    for file in existing_files:
        print(f"- {file}")
    
    while True:
        response = input("\nDo you want to proceed and override these files? (yes/no): ").lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def segment_audio(input_file, segment_length=10000):  # 10 seconds in milliseconds
    """
    Segment audio file into fixed-length chunks.
    segment_length: length of each segment in milliseconds (10 seconds)
    """
    print(f"Loading audio file: {input_file}")
    audio = AudioSegment.from_file(input_file)
    
    # Get the base name of the input file (without extension) for the segments directory
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    segments_dir = f"segments/{base_name}"
    
    # Calculate number of segments
    total_length = len(audio)
    num_segments = (total_length + segment_length - 1) // segment_length
    
    # Create output directory if it doesn't exist
    os.makedirs(segments_dir, exist_ok=True)
    
    # Export segments
    segment_files = []
    for i in range(num_segments):
        start = i * segment_length
        end = min((i + 1) * segment_length, total_length)
        segment = audio[start:end]
        output_file = f"{segments_dir}/segment_{i+1}.mp3"
        segment.export(output_file, format="mp3")
        segment_files.append(output_file)
        print(f"Created segment {i+1}: {output_file} ({end-start}ms)")
    
    return segment_files

def transcribe_segment(segment_file):
    """Transcribe a single audio segment"""
    print(f"Transcribing {segment_file}")
    with open(segment_file, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            language="en"
        )
    
    # Process the transcript
    segment_transcript = []
    for segment in transcript.segments:
        timestamp = format_timestamp(segment.start)
        segment_transcript.append(f"{timestamp} {segment.text.strip()}")
    
    return "\n".join(segment_transcript)

def format_timestamp(seconds):
    """Convert seconds to hh:mm:ss format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def transcribe_segments(segment_files, base_name):
    """Transcribe multiple audio segments and save each as a separate file"""
    all_transcripts = []
    transcripts_dir = f"transcripts/{base_name}"
    os.makedirs(transcripts_dir, exist_ok=True)
    
    for i, segment_file in enumerate(segment_files, 1):
        print(f"Transcribing segment {i}...")
        transcript = transcribe_segment(segment_file)
        all_transcripts.append(transcript)
        
        # Save individual transcript file
        transcript_file = f"{transcripts_dir}/segment_{i}.txt"
        with open(transcript_file, "w") as f:
            f.write(transcript)
        print(f"Saved transcript to {transcript_file}")
    
    return all_transcripts

def main():
    input_file = "audio/2025-04-24_18-10-14.m4a"
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Check for existing files
    existing_files = check_existing_files(input_file)
    if get_user_confirmation(existing_files):
        # Segment the audio
        segment_files = segment_audio(input_file)
        print(f"\nSegmentation complete. Created {len(segment_files)} segments in the 'segments/{base_name}' directory.")
        
        # Transcribe each segment
        all_transcripts = transcribe_segments(segment_files, base_name)
        
        # Save the final transcript
        output_file = f"transcripts/{base_name}.txt"
        os.makedirs("transcripts", exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n\n".join(all_transcripts))
        print(f"Transcript saved to {output_file}")
        
    # Ask if user wants to generate images and video
    while True:
        response = input("\nDo you want to generate images and video from the transcripts? (yes/no): ").lower()
        if response in ['yes', 'y']:
            process_segments_for_images(base_name)
            break
        elif response in ['no', 'n']:
            break
        else:
            print("Please enter 'yes' or 'no'")

if __name__ == "__main__":
    main() 