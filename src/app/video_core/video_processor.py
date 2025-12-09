"""
Video Processing Module - FFmpeg integration for merging videos
"""

import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable
import threading
from .cache_processor import CacheProcessor, CacheSettings

# Windows-specific flag to prevent CMD windows from appearing
if sys.platform == 'win32':
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


class VideoProcessor:
    """Handles video merging and processing using FFmpeg"""
    
    def __init__(self, cache_settings: Optional['CacheSettings'] = None):
        self.current_process = None
        self.is_processing = False
        self.cache_processor = CacheProcessor(cache_settings)
        
    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed and accessible"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def merge_videos(
        self,
        video_paths: List[str],
        output_path: str,
        codec: str = "H.264",
        video_format: str = ".mp4",
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None
    ):
        """
        Merge multiple videos into one using FFmpeg
        
        Args:
            video_paths: List of video file paths to merge
            output_path: Output file path (without extension)
            codec: Video codec to use
            video_format: Output format (e.g., ".mp4")
            progress_callback: Function to call with progress updates (percentage, message)
            completion_callback: Function to call when complete (success, message, output_path)
        """
        if not video_paths:
            if completion_callback:
                completion_callback(False, "No videos to merge", None)
            return
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(
            target=self._merge_videos_thread,
            args=(video_paths, output_path, codec, video_format, progress_callback, completion_callback)
        )
        thread.daemon = True
        thread.start()
    
    def merge_and_cache(
        self,
        video_paths: List[str],
        cache_path: str,
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None
    ):
        """
        Merge videos into a downscaled cache with preview support
        
        Args:
            video_paths: List of video file paths to merge
            cache_path: Base path for cached output (without extension)
            progress_callback: Function to call with progress updates (percentage, message)
            completion_callback: Function to call when complete (success, message, output_path)
        """
        if not video_paths:
            if completion_callback:
                completion_callback(False, "No videos to cache", None)
            return
        
        # Use cache processor to handle downscaling
        self.cache_processor.create_cache(
            video_paths=video_paths,
            cache_path=cache_path,
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )
    
    def _merge_videos_thread(
        self,
        video_paths: List[str],
        output_path: str,
        codec: str,
        video_format: str,
        progress_callback: Optional[Callable],
        completion_callback: Optional[Callable]
    ):
        """Internal thread function for video merging"""
        print("[VIDEO_PROCESSOR] Starting merge thread")
        self.is_processing = True
        output_file = f"{video_format.lower()}" if output_path.endswith(video_format.lower()) else f"{output_path}{video_format.lower()}"
        print(f"[VIDEO_PROCESSOR] Output file: {output_file}")
        
        try:
            print("[VIDEO_PROCESSOR] Creating output directory...")
            # Ensure output directory exists
            output_dir = Path(output_file).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"[VIDEO_PROCESSOR] Output directory ready: {output_dir}")
            
            # Create concat file for FFmpeg
            print("[VIDEO_PROCESSOR] Creating concat file...")
            concat_file = self._create_concat_file(video_paths)
            print(f"[VIDEO_PROCESSOR] Concat file created: {concat_file}")
            
            if progress_callback:
                progress_callback(10, "Preparing video merge...")
            
            # Map codec names to FFmpeg codec names
            codec_map = {
                "H.264": "libx264",
                "H.265": "libx265",
                "VP8": "libvpx",
                "VP9": "libvpx-vp9",
                "MPEG-4": "mpeg4",
                "MPEG-2": "mpeg2video",
                "ProRes": "prores",
                "Theora": "libtheora",
                "AV1": "libaom-av1",
                "WMV": "wmv2",
            }
            
            ffmpeg_codec = codec_map.get(codec, "libx264")
            print(f"[VIDEO_PROCESSOR] Using codec: {codec} -> {ffmpeg_codec}")
            
            # Build FFmpeg command
            # Re-encode to ensure consistent codec, framerate, and pixel format
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", ffmpeg_codec,
                "-c:a", "aac",  # Audio codec
                "-b:a", "192k",  # Audio bitrate
                "-ar", "48000",  # Audio sample rate
                "-ac", "2",  # Stereo audio
                "-pix_fmt", "yuv420p",  # Ensure consistent pixel format
                "-r", "30",  # Force consistent framerate
                "-preset", "medium",  # Encoding speed/quality balance
                "-crf", "23",  # Quality (lower = better, 18-28 recommended)
                "-movflags", "+faststart",  # Web optimization
                "-max_muxing_queue_size", "1024",  # Prevent muxing errors
                "-y",  # Overwrite output file
                output_file
            ]
            
            
            if progress_callback:
                progress_callback(30, "Merging videos...")
            
            print("[VIDEO_PROCESSOR] Building FFmpeg command...")
            print(f"[VIDEO_PROCESSOR] Command: ffmpeg -f concat -safe 0 -i {concat_file} -c:v {ffmpeg_codec} ...")
            
            # Run FFmpeg process
            print("[VIDEO_PROCESSOR] Starting FFmpeg process...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print(f"[VIDEO_PROCESSOR] FFmpeg process started (PID: {process.pid})")
            
            self.current_process = process
            
            # Read output for progress tracking
            print("[VIDEO_PROCESSOR] Getting total duration...")
            total_duration = self._get_total_duration(video_paths)
            print(f"[VIDEO_PROCESSOR] Total duration: {total_duration}s")
            
            print("[VIDEO_PROCESSOR] Reading FFmpeg output...")
            line_count = 0
            for line in process.stderr:
                line_count += 1
                if line_count % 30 == 0:  # Print every 30th line to avoid spam
                    print(f"[VIDEO_PROCESSOR] Processing... (line {line_count})")
                if progress_callback and "time=" in line:
                    # Parse current time from FFmpeg output
                    current_time = self._parse_time_from_ffmpeg(line)
                    if current_time and total_duration:
                        percentage = min(int((current_time / total_duration) * 60) + 30, 90)
                        progress_callback(percentage, f"Processing... {percentage}%")
            
            # Wait for process to complete
            print("[VIDEO_PROCESSOR] Waiting for FFmpeg to complete...")
            process.wait()
            print(f"[VIDEO_PROCESSOR] FFmpeg finished with return code: {process.returncode}")
            
            # Clean up concat file
            print("[VIDEO_PROCESSOR] Cleaning up concat file...")
            if os.path.exists(concat_file):
                os.remove(concat_file)
                print("[VIDEO_PROCESSOR] Concat file removed")
            
            if process.returncode == 0:
                print("[VIDEO_PROCESSOR] Merge successful!")
                if progress_callback:
                    progress_callback(100, "Merge complete!")
                if completion_callback:
                    completion_callback(True, f"Video saved: {output_file}", output_file)
            else:
                print(f"[VIDEO_PROCESSOR] Merge failed with return code {process.returncode}")
                error_msg = "FFmpeg process failed"
                if completion_callback:
                    completion_callback(False, error_msg, None)
                    
        except Exception as e:
            print(f"[VIDEO_PROCESSOR] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            if completion_callback:
                completion_callback(False, f"Error: {str(e)}", None)
        finally:
            print("[VIDEO_PROCESSOR] Cleaning up...")
            self.is_processing = False
            self.current_process = None
            print("[VIDEO_PROCESSOR] Merge thread finished")
    
    def _create_concat_file(self, video_paths: List[str]) -> str:
        """Create temporary concat file for FFmpeg"""
        concat_file = "temp_concat_list.txt"
        
        with open(concat_file, "w", encoding="utf-8") as f:
            for video_path in video_paths:
                # Convert to absolute path and escape special characters
                abs_path = os.path.abspath(video_path).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")
        
        return concat_file
    
    def _get_total_duration(self, video_paths: List[str]) -> Optional[float]:
        """Get total duration of all videos in seconds"""
        try:
            total = 0
            for video_path in video_paths:
                cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                      creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                duration = float(result.stdout.strip())
                total += duration
            return total
        except:
            return None
    
    def _parse_time_from_ffmpeg(self, line: str) -> Optional[float]:
        """Parse current time from FFmpeg stderr output"""
        try:
            if "time=" in line:
                time_str = line.split("time=")[1].split()[0]
                # Parse HH:MM:SS.ms format
                parts = time_str.split(":")
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return None
    
    def cancel_processing(self):
        """Cancel current processing operation"""
        if self.current_process:
            self.current_process.terminate()
            self.is_processing = False
