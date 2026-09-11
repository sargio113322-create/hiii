# Python-এর অফিসিয়াল ইমেজ ব্যবহার
FROM python:3.11-slim

# সিস্টেম ডিপেন্ডেন্সি ইনস্টল (ffmpeg অত্যন্ত জরুরি)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ওয়ার্কিং ডিরেক্টরি সেট
WORKDIR /app

# প্রথমে requirements কপি ও ইনস্টল (Docker ক্যাশে ভালোভাবে ব্যবহার করতে)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# বাকি কোড কপি
COPY . .

# বট রান
CMD ["python", "bot.py"]
