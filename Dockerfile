# Use Ubuntu as the base image
FROM ubuntu:22.04

# Install necessary packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up a working directory
# WORKDIR /app

COPY . /app

# Install any Python dependencies if needed
RUN pip install -r /app/requirements.txt

# Cleanup unnecessary files (optional)
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# TOKEN should be defined at runtime
ENV TOKEN=1234

CMD python3 /app/src/bot.py --token ${TOKEN}
