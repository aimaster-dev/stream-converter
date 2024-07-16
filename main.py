from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import subprocess
import os
import threading
import time

app = Flask(__name__)
CORS(app)

HLS_FOLDER = os.path.join(os.path.dirname(__file__), 'hls')
if not os.path.exists(HLS_FOLDER):
    os.makedirs(HLS_FOLDER)

# Dictionary to keep track of FFmpeg processes
processes = {}

def convert_rtsp_to_hls(rtsp_url, stream_name):
    stream_folder = os.path.join(HLS_FOLDER, stream_name)
    if not os.path.exists(stream_folder):
        os.makedirs(stream_folder)
    
    ffmpeg_command = [
        'ffmpeg', '-rtsp_transport', 'tcp', '-analyzeduration', '50000000', '-probesize', '50000000',
        '-i', rtsp_url,
        '-map', '0:v:0', '-map', '0:a:0',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
        '-f', 'hls', '-hls_time', '4', '-hls_list_size', '3',  # Keep only the last 3 segments
        '-hls_flags', 'delete_segments', '-hls_delete_threshold', '1', # Delete segments once 4 exist
        os.path.join(stream_folder, 'index.m3u8')
    ]

    log_file = os.path.join(stream_folder, 'ffmpeg.log')
    with open(log_file, 'w') as log:
        process = subprocess.Popen(ffmpeg_command, stdout=log, stderr=log)
        # Save the process to the dictionary
        processes[stream_name] = process
        process.wait()

@app.route('/stream/<stream_name>/<path:filename>')
def stream(stream_name, filename):
    return send_from_directory(os.path.join(HLS_FOLDER, stream_name), filename)

@app.route('/start_stream', methods=['POST'])
def start_stream():
    data = request.json
    rtsp_url = data.get('rtsp_url')
    stream_name = data.get('stream_name')
    
    if not rtsp_url or not stream_name:
        return jsonify({'error': 'Invalid request, rtsp_url and stream_name are required'}), 400

    thread = threading.Thread(target=convert_rtsp_to_hls, args=(rtsp_url, stream_name))
    thread.start()
    
    return jsonify({'message': 'Stream started', 'stream_name': stream_name}), 200

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    data = request.json
    stream_name = data.get('stream_name')
    
    if not stream_name:
        return jsonify({'error': 'Invalid request, stream_name is required'}), 400

    # Check if the stream is running
    if stream_name in processes:
        # Terminate the process
        process = processes.pop(stream_name)
        process.terminate()
        return jsonify({'message': f'Stream {stream_name} stopped'}), 200
    else:
        return jsonify({'error': f'Stream {stream_name} not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
