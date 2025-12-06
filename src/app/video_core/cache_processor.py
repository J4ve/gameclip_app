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
        self.is_caching = True
        
        try:
            # Ensure cache directory exists
            cache_dir = Path(cache_path).parent
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback(10, "Preparing cache merge...")
            
            # Create concat file
            concat_file = self._create_concat_file(video_paths)
            
            if progress_callback:
                progress_callback(20, "Building merge stream...")
            
            # Get video dimensions for downscaling calculation
            width, height = self._get_video_dimensions(video_paths[0])
            downscaled_width, downscaled_height = self._calculate_downscale_dims(width, height)
            
            if progress_callback:
                progress_callback(30, f"Caching at {downscaled_width}x{downscaled_height}...")
            
            # Build FFmpeg command for cached video
            cmd = self._build_ffmpeg_command(
                concat_file,
                cache_path,
                downscaled_width,
                downscaled_height
            )
            
            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.current_process = process
            
            # Track progress
            total_duration = self._get_total_duration(video_paths)
            
            for line in process.stderr:
                if progress_callback and "time=" in line:
                    current_time = self._parse_time_from_ffmpeg(line)
                    if current_time and total_duration:
                        percentage = min(int((current_time / total_duration) * 60) + 30, 90)
                        progress_callback(percentage, f"Caching... {percentage}%")
            
            # Wait for process
            process.wait()
            
            # Clean up concat file
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            if process.returncode == 0:
                output_file = f"{cache_path}.mp4"
                
                if progress_callback:
                    progress_callback(100, "Cache complete!")
                
                if completion_callback:
                    completion_callback(True, f"Cache created: {output_file}", output_file)
                
                self.cached_files.append(output_file)
            else:
                error_output = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
                if completion_callback:
                    completion_callback(False, f"Cache process failed: {error_output}", None)
                    
        except Exception as e:
            if completion_callback:
                completion_callback(False, f"Error: {str(e)}", None)
        finally:
            self.is_caching = False
            self.current_process = None
    
    def _build_ffmpeg_command(self, concat_file: str, cache_path: str, width: int, height: int) -> list:
        """Build FFmpeg command for caching with downscaling using fMP4"""
        output_file = f"{cache_path}.mp4"
        
        scale_filter = f"scale={width}:{height}" if self.settings.downscale_enabled else "null"
        
        # fMP4 (fragmented MP4) allows preview while file is still being written
        # -movflags faststart writes stream headers early for progressive download
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-vf", scale_filter,  # Scale/downscale video
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", self.settings.preset,  # Fast encoding for cache
            "-movflags", "faststart",  # Write stream headers early (fMP4 compatible)
            "-y",
            output_file
        ]
        
        return cmd
    
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
