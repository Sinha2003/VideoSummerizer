from flask import Flask, render_template, request
from transformers import pipeline
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from googletrans import Translator  # Google Translator for handling non-English transcripts

app = Flask(__name__)

# Initialize the translator and summarizer
translator = Translator()
summarizer = pipeline('summarization')

# Function to summarize video
def summarize_video(video_url):
    # Extract video ID
    if "youtube.com" in video_url:
        video_id = video_url.split("v=")[1].split("&")[0]
    elif "youtu.be" in video_url:
        video_id = video_url.split("/")[-1]
    else:
        return "Invalid YouTube URL format."

    # Try to get transcript in English first
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except NoTranscriptFound:
        # If English transcript is not available, fallback to auto-generated transcript in Hindi
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
            # Translate Hindi transcript to English
            transcript_text = " ".join([i['text'] for i in transcript])
            transcript_text = translator.translate(transcript_text, src='hi', dest='en').text
        except NoTranscriptFound:
            return "Transcripts not available in English or Hindi. Try another video."
        except TranscriptsDisabled:
            return "Transcripts are disabled for this video."
        except Exception as e:
            return f"Error fetching transcript: {e}"
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except Exception as e:
        return f"Error fetching transcript: {e}"
    else:
        # Combine the English transcript text if it was successfully fetched
        transcript_text = " ".join([i['text'] for i in transcript])

    # Break the transcript into manageable chunks
    chunk_size = 1000
    num_chunks = (len(transcript_text) // chunk_size) + 1
    summarized_text = []

    # Summarize each chunk
    for i in range(num_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        chunk = transcript_text[start:end]
        if len(chunk) > 0:
            out = summarizer(chunk, max_length=80, min_length=30, do_sample=False)
            summary = out[0]['summary_text']
            summarized_text.append(summary)

    # Combine all summarized chunks into one paragraph
    final_summary = " ".join(summarized_text)
    return final_summary

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("youtube_url")
        summary = summarize_video(video_url)
        return render_template("index.html", summary=summary, video_url=video_url)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
