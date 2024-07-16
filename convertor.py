import ffmpeg

def convert_video(input_file, output_file):
    try:
        # Using ffmpeg to convert the video file to MP4 format
        ffmpeg.input(input_file).output(output_file, vcodec='libx264', acodec='aac').run()
        print(f"Video conversion successful! Output file: {output_file}")
    except ffmpeg.Error as e:
        print(f"An error occurred during video conversion: {e}")

if __name__ == "__main__":
    # Path to the input video file (recorded from the camera RTSP stream)
    input_file = 'camera1_20240530193028.mp4'
    # Path to the output video file
    output_file = 'converted_video.mp4'
    
    # Convert the video
    convert_video(input_file, output_file)