# Use official LiveKit Server image as base
FROM livekit/livekit-server:latest

# Set working directory inside container
WORKDIR /livekit

# Copy your config file into the container
COPY livekit.yaml /livekit/livekit.yaml

# Expose necessary ports
# 7880 - API/HTTP
# 7881 - RTC TCP
# 7882 - RTC UDP
EXPOSE 7880 7881 7882/udp

# Run LiveKit Server with the config file
CMD ["livekit-server", "--config", "/livekit/livekit.yaml"]
