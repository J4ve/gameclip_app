"""
Cache Processor - Handles incremental video caching with downscaling
Supports preview-friendly formats (HLS/DASH) for live preview while writing
"""

import subprocess
import os
import sys
from pathlib import Path
from typing import Optional, Callable
import threading

# Windows-specific flag to prevent CMD windows from appearing
if sys.platform == 'win32':
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0
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
        
        Intelligently decides whether to generate preview based on video codecs.
        - Same codec videos: Fast stream copy (instant preview)
        - Mixed codecs: Skip preview (too slow to re-encode)
        
        Args:
            video_paths: List of video file paths to merge and cache
            cache_path: Base path for cache output (without extension)
            progress_callback: Function(percentage, message)
            completion_callback: Function(success, message, manifest_or_file_path)
        
        Returns:
            Path to cached video or None if skipped
        """
        if not video_paths:
            if completion_callback:
                completion_callback(False, "No videos to cache", None)
            return None
        
        # Check if all videos have the same codec
        if self._has_mixed_codecs(video_paths):
            # Skip preview for mixed properties - too slow or causes issues
            if completion_callback:
                completion_callback(
                    True, 
                    "Preview skipped - videos have different properties (codec/resolution/framerate). Use \"Save Video\" for final merge.", 
                    None
                )
            return None
        
        # Same codec - use fast stream copy for instant preview
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
            print("[CACHE_PROCESSOR] Creating cache directory...")
            cache_dir = Path(cache_path).parent
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[CACHE_PROCESSOR] Cache directory ready: {cache_dir}")
            
            if progress_callback:
                progress_callback(10, "Preparing cache merge...")
            
            # Create concat file
            print("[CACHE_PROCESSOR] Creating concat file...")
            concat_file = self._create_concat_file(video_paths)
            print(f"[CACHE_PROCESSOR] Concat file created: {concat_file}")
            
            if progress_callback:
                progress_callback(20, "Building merge stream...")
            
            # Get video dimensions for downscaling calculation
            print("[CACHE_PROCESSOR] Getting video dimensions...")
            width, height = self._get_video_dimensions(video_paths[0])
            print(f"[CACHE_PROCESSOR] Original dimensions: {width}x{height}")
            
            downscaled_width, downscaled_height = self._calculate_downscale_dims(width, height)
            print(f"[CACHE_PROCESSOR] Target dimensions: {downscaled_width}x{downscaled_height}")
            
            if progress_callback:
                progress_callback(30, f"Caching at {downscaled_width}x{downscaled_height}...")
            
            # Build FFmpeg command for cached video
            print("[CACHE_PROCESSOR] Building FFmpeg command...")
            cmd = self._build_ffmpeg_command(
                concat_file,
                cache_path,
                downscaled_width,
                downscaled_height
            )
            print(f"[CACHE_PROCESSOR] Command: ffmpeg -f concat -safe 0 ...")
            
            # Execute FFmpeg
            print("[CACHE_PROCESSOR] Starting FFmpeg process...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print(f"[CACHE_PROCESSOR] FFmpeg process started (PID: {process.pid})")
            
            self.current_process = process
            
            # Track progress
            print("[CACHE_PROCESSOR] Getting total duration...")
            total_duration = self._get_total_duration(video_paths)
            print(f"[CACHE_PROCESSOR] Total duration: {total_duration}s")
            
            print("[CACHE_PROCESSOR] Reading FFmpeg output...")
            line_count = 0
            for line in process.stderr:
                line_count += 1
                if line_count % 30 == 0:  # Print every 30th line to avoid spam
                    print(f"[CACHE_PROCESSOR] Processing... (line {line_count})")
                if progress_callback and "time=" in line:
                    current_time = self._parse_time_from_ffmpeg(line)
                    if current_time and total_duration:
                        percentage = min(int((current_time / total_duration) * 60) + 30, 90)
                        progress_callback(percentage, f"Caching... {percentage}%")
            
            # Wait for process
            print("[CACHE_PROCESSOR] Waiting for FFmpeg to complete...")
            process.wait()
            print(f"[CACHE_PROCESSOR] FFmpeg finished with return code: {process.returncode}")
            
            # Clean up concat file (with retry for Windows file locks)
            print("[CACHE_PROCESSOR] Cleaning up concat file...")
            if os.path.exists(concat_file):
                try:
                    import time
                    time.sleep(0.1)  # Brief delay for Windows to release file
                    os.remove(concat_file)
                    print("[CACHE_PROCESSOR] Concat file removed")
                except Exception as e:
                    print(f"[CACHE_PROCESSOR] Concat file cleanup skipped: {e}")
            
            if process.returncode == 0:
                output_file = f"{cache_path}.mp4"
                print(f"[CACHE_PROCESSOR] Cache successful! Output: {output_file}")
                
                if progress_callback:
                    progress_callback(100, "Cache complete!")
                
                if completion_callback:
                    completion_callback(True, f"Cache created: {output_file}", output_file)
                
                self.cached_files.append(output_file)
            else:
                print(f"[CACHE_PROCESSOR] Cache failed with return code {process.returncode}")
                error_output = process.stderr.read() if hasattr(process.stderr, 'read') else "Unknown error"
                if completion_callback:
                    completion_callback(False, f"Cache process failed: {error_output}", None)
                    
        except Exception as e:
            print(f"[CACHE_PROCESSOR] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            if completion_callback:
                completion_callback(False, f"Error: {str(e)}", None)
        finally:
            print("[CACHE_PROCESSOR] Cleaning up...")
            self.is_caching = False
            self.current_process = None
            print("[CACHE_PROCESSOR] Cache thread finished")
    
    def _has_mixed_codecs(self, video_paths: list) -> bool:
        """
        Check if videos have different codecs, resolutions, or framerates.
        Stream copy only works reliably when ALL properties match.
        """
        try:
            video_properties = []
            for video_path in video_paths:
                cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name,width,height,r_frame_rate",
                    "-of", "json",
                    video_path
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5,
                                      creationflags=CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                
                import json
                data = json.loads(result.stdout)
                stream = data['streams'][0]
                
                # Create a tuple of (codec, width, height, framerate)
                props = (
                    stream['codec_name'],
                    stream['width'],
                    stream['height'],
                    stream['r_frame_rate']
                )
                video_properties.append(props)
            
            # Check if all properties are identical
            first_props = video_properties[0]
            for props in video_properties[1:]:
                if props != first_props:
                    print(f"[CACHE_PROCESSOR] Mixed properties detected:")
                    print(f"  First video: codec={first_props[0]}, {first_props[1]}x{first_props[2]}, {first_props[3]} fps")
                    print(f"  Other video: codec={props[0]}, {props[1]}x{props[2]}, {props[3]} fps")
                    return True
            
            print(f"[CACHE_PROCESSOR] All videos match: codec={first_props[0]}, {first_props[1]}x{first_props[2]}, {first_props[3]} fps")
            return False
            
        except Exception as e:
            print(f"[CACHE_PROCESSOR] Property detection failed: {e}")
            # If detection fails, assume mixed (safer - skip preview)
            return True
    
    def _build_ffmpeg_command(self, concat_file: str, cache_path: str, width: int, height: int) -> list:
        """
        Build FFmpeg command for caching - FAST stream copy for same-codec videos
        
        This method is only called when all videos have the same codec.
        Uses stream copy for instant preview (1-2 seconds).
        """
        output_file = f"{cache_path}.mp4"
        
        # Stream copy - instant for same-codec videos!
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",  # No re-encoding - instant!
            "-movflags", "+faststart",
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
