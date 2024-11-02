#!/bin/bash

# Wait for NiFi to be ready
wait_for_nifi() {
    echo "Waiting for NiFi to start..."
    while true; do
        if curl -s -f http://localhost:8080/nifi/ > /dev/null; then
            echo "NiFi is up!"
            break
        fi
        sleep 5
    done
}

# Start NiFi in the background
../bin/nifi.sh start &

# Wait for NiFi to be ready
wait_for_nifi

# Use NiFi Toolkit to upload and start flows
for flow in /opt/nifi/nifi-current/conf/flows/*.xml; do
    if [ -f "$flow" ]; then
        echo "Loading flow: $flow"
        ../bin/nifi.sh cli load-flow -f "$flow"
    fi
done

# Keep container running
tail -f ../logs/nifi-app.log