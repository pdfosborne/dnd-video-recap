# D&D AI Summary

This script segments audio recordings and transcribes them using OpenAI's Whisper API, identifying different speakers and formatting the output with timestamps.

The script segments the audio into 10s chunks, transcribes them and then produces an image with OpenAI's new API method.

Lastly images are composed into a single video with audio added appropriately as shown in the following output example:

<video width="320" height="240" controls align='center'>
  <source src="https://rawcdn.githack.com/pdfosborne/dnd-video-recap/e5270f2961a209034b70d61b26352af2c7292841/examples/example_2.mp4" type="video/mp4">
</video>

I would suggest asking images for no more than 10 segments at a time at this stage. The code is experimental as a proof of concept and need significant further development.

API usage costs approximately $0.10 per minute of audio to transcribe and then each image costs another $0.10 in my experience. Your usage may vary, please ensure you track your API usage and I take no responsibility for accidental overuse.

This was created as a personal project. Please feel free to report issues but I take no responsibility for unintended usage of the project or deviations. Use at your own risk, and please act responsibly.

## Requirements

- Python 3.7+
- FFmpeg (required by pydub)
- OpenAI API key

## Installation

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg:
- On Ubuntu/Debian: `sudo apt-get install ffmpeg`
- On macOS: `brew install ffmpeg`
- On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

3. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Place your audio file in the `audio` directory
2. Run the script:
```bash
python transcribe.py
```

The script will:
1. Segment the audio into 4-7 minute chunks based on silence detection
2. Transcribe each segment using OpenAI's Whisper API
3. Identify different speakers and assign them unique IDs
4. Generate a transcript with timestamps in the format: `user N hh:mm:ss text`

The output will be saved in `transcript.txt`.

## Output Format

The transcript will be formatted as:
```
user 1 00:00:00 Hello, how are you?
user 2 00:00:03 I'm doing well, thank you!
...
```

Where:
- `user N` is the speaker identifier
- `hh:mm:ss` is the timestamp
- The rest is the transcribed text 
