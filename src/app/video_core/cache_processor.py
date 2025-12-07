"""
Cache Processor - Handles incremental video caching with downscaling
Supports preview-friendly formats (HLS/DASH) for live preview while writing
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Callable
import threading
from datetime import datetime


class CacheSettings:
    """Settings for video caching and downscaling"""
    
    def __init__(
        self,
        downscale_enabled: bool = True,
        downscale_factor: float = 0.5,  # 0.5 = 50% of original size
        preset: str = "ultrafast",  # ultrafast, superfast, veryfast, faster, fast, medium
        use_hls: bool = True,
        segment_duration: int = 4,  # HLS segment duration in seconds
        max_segments: int = 10  # Keep last N segments for streaming
    ):
        self.downscale_enabled = downscale_enabled
        self.downscale_factor = downscale_factor
        self.preset = preset
        self.use_hls = use_hls
        self.segment_duration = segment_duration
        self.max_segments = max_segments


class CacheProcessor:
    """Handles video caching with downscaling and preview-friendly format"""
    
    def __init__(self, cache_settings: Optional[CacheSettings] = None):
        self.settings = cache_settings or CacheSettings()
        self.current_process = None
        self.is_caching = False
        self.cached_files = []
        
    def create_cache(
        self,
        video_paths: list,
        cache_path: str,
        progress_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Create cached merged video with downscaling
        
        Args:
            video_paths: List of video file paths to merge and cache
            cache_path: Base path for cache output (without extension)
            progress_callback: Function(percentage, message)
            completion_callback: Function(success, message, manifest_or_file_path)
        
        Returns:
            Path to cached video or HLS manifest
        """
        if not video_paths:
            if completion_callback:
                completion_callback(False, "No videos to cache", None)
            return None
        
        # Run in separate thread
        thread = threading.Thread(
            target=self._cache_thread,
            args=(video_paths, cache_path, progress_callback, completion_callback)
        )
        thread.daemon = True
        thread.start()
        
        return cache_path
    
    def _cache_thread(
        self,
        video_paths: list,
        cache_path: str,
        progress_callback: Optional[Callable],
        completion_callback: Optional[Callable]
    ):
        """Internal thread function for caching"""
        print("[CACHE_PROCESSOR] Starting cache thread")
        self.is_caching = True
        
        try:
            # Ensure cache directory exists
            cache_dir = Path(cache_path).parent
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback(30, "Creating preview...")
            
            # Create concat file
            concat_file = self._create_concat_file(video_paths)
            
            # Build FFmpeg command for cached video
            cmd = self._build_ffmpeg_command(concat_file, cache_path)
            
            # Execute FFmpeg - must read stderr or it will block
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.current_process = process
            
            # Consume stderr to prevent blocking (but don't process it)
            for _ in process.stderr:
                pass
            
            # Wait for process
            process.wait()
            
            # Clean up concat file
            try:
                if os.path.exists(concat_file):
                    import time
                    time.sleep(0.1)
                    os.remove(concat_file)
            except:
                pass
            
            output_file = f"{cache_path}.mp4"
            
            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100, "Preview ready!")
                
                if completion_callback:
                    completion_callback(True, f"Preview ready", output_file)
                
                self.cached_files.append(output_file)
            else:
                if completion_callback:
                    completion_callback(False, "Preview failed", None)
                    
        except Exception as e:
            if completion_callback:
                completion_callback(False, f"Error: {str(e)}", None)
        finally:
            self.is_caching = False
            self.current_process = None
    
    def _build_ffmpeg_command(self, concat_file: str, cache_path: str) -> list:
        """
        Build FFmpeg command - FAST re-encoding with consistency
        Uses ultrafast preset with minimal processing for speed
        """
        output_file = f"{cache_path}.mp4"
        
        # Must re-encode for compatibility, but use absolute fastest settings
        return [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",  # Minimal buffering
            "-crf", "35",  # Very low quality = very fast
            "-g", "250",  # Huge GOP = fewer keyframes
            "-sc_threshold", "0",  # Disable scene detection
            "-bf", "0",  # No B-frames
            "-refs", "1",  # Single reference frame
            "-c:a", "aac",
            "-b:a", "64k",  # Very low audio bitrate
            "-ar", "22050",  # Half sample rate
            "-ac", "1",  # Mono audio
            "-pix_fmt", "yuv420p",
            "-r", "24",  # Lower framerate
            "-threads", "0",
            "-y",
            output_file
        ]
    
    def _calculate_downscale_dims(self, original_width: int, original_height: int) -> tuple:
        """Calculate downscaled dimensions maintaining aspect ratio"""
        if not self.settings.downscale_enabled:
            return original_width, original_height
        
        factor = self.settings.downscale_factor
        new_width = int(original_width * factor)
        new_height = int(original_height * factor)
        
        # Ensure dimensions are even (required by many codecs)
        new_width = (new_width // 2) * 2
        new_height = (new_height // 2) * 2
        
        return new_width, new_height
    
    def _get_video_dimensions(self, video_path: str) -> tuple:
        """Get video width and height"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                video_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            width, height = map(int, result.stdout.strip().split('x'))
            return width, height
        except Exception:
            # Default to 1920x1080 if unable to detect
            return 1920, 1080
    
    def _create_concat_file(self, video_paths: list) -> str:
        """Create temporary concat file for FFmpeg"""
        concat_file = "temp_concat_list.txt"
        
        with open(concat_file, "w", encoding="utf-8") as f:
            for video_path in video_paths:
                abs_path = os.path.abspath(video_path).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")
        
        return concat_file
    
    def _get_total_duration(self, video_paths: list) -> Optional[float]:
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
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                duration = float(result.stdout.strip())
                total += duration
            return total
        except Exception:
            return None
    
    def _parse_time_from_ffmpeg(self, line: str) -> Optional[float]:
        """Parse current time from FFmpeg stderr output"""
        try:
            if "time=" in line:
                time_str = line.split("time=")[1].split()[0]
                parts = time_str.split(":")
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except Exception:
            pass
        return None
    
    def clear_cache(self, max_age_hours: int = 24):
        """Clear old cache files"""
        for cache_file in self.cached_files[:]:
            if os.path.exists(cache_file):
                try:
                    file_age = (datetime.now().timestamp() - os.path.getmtime(cache_file)) / 3600
                    if file_age > max_age_hours:
                        os.remove(cache_file)
                        self.cached_files.remove(cache_file)
                except Exception:
                    pass
    
    def clear_all_cache(self):
        """Clear ALL cached files immediately"""
        for cache_file in self.cached_files[:]:
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    self.cached_files.remove(cache_file)
                except Exception:
                    pass
    
    def cancel_caching(self):
        """Cancel current caching operation"""
        if self.current_process:
            self.current_process.terminate()
            self.is_caching = False
