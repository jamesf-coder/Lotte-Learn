# Use Ubuntu as the base image
FROM ubuntu:22.04

# Install necessary packages
RUN apt-get update && \
    apt-get install -y python3 git python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /app

# Clone your Python application from the GitHub repository
RUN git clone https://github.com/jamesf-coder/Lottie-Learn.git .

# Install any Python dependencies if needed
RUN pip install -r /app/Lottie-Learn/requirements.txt

# Create a systemd service unit file
RUN echo "[Unit]" > /etc/systemd/system/lottielearnbot.service && \
    echo "Description=LottieLearnBot" >> /etc/systemd/system/lottielearnbot.service && \
    echo "" >> /etc/systemd/system/lottielearnbot.service && \
    echo "[Service]" >> /etc/systemd/system/lottielearnbot.service && \
    echo "ExecStart=/usr/bin/python3 /app/Lottie-Learn/src/bot.py" >> /etc/systemd/system/lottielearnbot.service && \
    echo "Restart=always" >> /etc/systemd/system/lottielearnbot.service && \
    echo "User=nobody" >> /etc/systemd/system/lottielearnbot.service && \
    echo "" >> /etc/systemd/system/lottielearnbot.service && \
    echo "[Install]" >> /etc/systemd/system/lottielearnbot.service && \
    echo "WantedBy=multi-user.target" >> /etc/systemd/system/lottielearnbot.service

# Enable and start the systemd service
RUN systemctl enable lottielearnbot.service

# Expose any necessary ports
# EXPOSE 80

# Start the systemd init system
CMD ["/lib/systemd/systemd"]

# Cleanup unnecessary files (optional)
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
