"""
Tests for Cache Processor - Downscaled video caching functionality
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.video_core.cache_processor import CacheProcessor, CacheSettings


@pytest.fixture
def cache_settings():
    """Create cache settings for testing"""
    return CacheSettings(
        downscale_enabled=True,
        downscale_factor=0.5,
        preset="ultrafast",
        use_hls=False
    )


@pytest.fixture
def cache_processor(cache_settings):
    """Create a CacheProcessor instance for testing"""
    return CacheProcessor(cache_settings)


@pytest.fixture
def sample_video_paths(tmp_path):
    """Create sample video file paths for testing"""
    video1 = tmp_path / "video1.mp4"
    video2 = tmp_path / "video2.mp4"
    
    video1.touch()
    video2.touch()
    
    return [str(video1), str(video2)]


@pytest.fixture
def cache_path(tmp_path):
    """Create cache path for testing"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    return str(cache_dir / "cached_video")


class TestCacheSettings:
    """Test CacheSettings configuration"""
    
    def test_default_settings(self):
        """Test default cache settings"""
        settings = CacheSettings()
        
        assert settings.downscale_enabled is True
        assert settings.downscale_factor == 0.5
        assert settings.preset == "ultrafast"
        assert settings.use_hls is True
        assert settings.segment_duration == 4
        assert settings.max_segments == 10
    
    def test_custom_settings(self):
        """Test custom cache settings"""
        settings = CacheSettings(
            downscale_enabled=False,
            downscale_factor=0.25,
            preset="fast",
            use_hls=False,
            segment_duration=2,
            max_segments=5
        )
        
        assert settings.downscale_enabled is False
        assert settings.downscale_factor == 0.25
        assert settings.preset == "fast"
        assert settings.use_hls is False
        assert settings.segment_duration == 2
        assert settings.max_segments == 5


class TestDownscaleCalculations:
    """Test video downscaling dimension calculations"""
    
    def test_calculate_downscale_dims_50_percent(self, cache_processor):
        """Test 50% downscaling calculation"""
        width, height = cache_processor._calculate_downscale_dims(1920, 1080)
        
        assert width == 960
        assert height == 540
        assert width % 2 == 0  # Must be even
        assert height % 2 == 0
    
    def test_calculate_downscale_dims_disabled(self, cache_processor):
        """Test downscaling when disabled"""
        cache_processor.settings.downscale_enabled = False
        width, height = cache_processor._calculate_downscale_dims(1920, 1080)
        
        assert width == 1920
        assert height == 1080
    
    def test_calculate_downscale_dims_odd_numbers(self, cache_processor):
        """Test that odd dimensions are rounded to even numbers"""
        width, height = cache_processor._calculate_downscale_dims(1919, 1079)
        
        # Should round down to nearest even number
        assert width % 2 == 0
        assert height % 2 == 0
    
    def test_different_downscale_factors(self):
        """Test various downscale factors"""
        test_cases = [
            (0.25, 1920, 1080, 480, 270),
            (0.75, 1920, 1080, 1440, 810),
            (0.33, 1920, 1080, 632, 356),  # Rounded to even
        ]
        
        for factor, orig_w, orig_h, expected_w, expected_h in test_cases:
            settings = CacheSettings(downscale_factor=factor)
            processor = CacheProcessor(settings)
            
            width, height = processor._calculate_downscale_dims(orig_w, orig_h)
            assert width == expected_w
            assert height == expected_h


class TestVideoDimensionDetection:
    """Test video dimension detection"""
    
    @patch('subprocess.run')
    def test_get_video_dimensions_success(self, mock_run, cache_processor):
        """Test successful dimension detection"""
        mock_run.return_value = Mock(stdout="1920x1080\n", returncode=0)
        
        width, height = cache_processor._get_video_dimensions("test_video.mp4")
        
        assert width == 1920
        assert height == 1080
        
        # Verify ffprobe command
        args = mock_run.call_args[0][0]
        assert "ffprobe" in args
        assert "-show_entries" in args
        assert "stream=width,height" in args
    
    @patch('subprocess.run')
    def test_get_video_dimensions_failure_returns_default(self, mock_run, cache_processor):
        """Test that default dimensions are returned on failure"""
        mock_run.side_effect = Exception("FFprobe error")
        
        width, height = cache_processor._get_video_dimensions("test_video.mp4")
        
        assert width == 1920  # Default
        assert height == 1080  # Default
    
    @patch('subprocess.run')
    def test_get_video_dimensions_timeout(self, mock_run, cache_processor):
        """Test timeout handling in dimension detection"""
        mock_run.return_value = Mock(stdout="1920x1080\n", returncode=0)
        
        cache_processor._get_video_dimensions("test_video.mp4")
        
        # Verify timeout is set
        kwargs = mock_run.call_args[1]
        assert 'timeout' in kwargs
        assert kwargs['timeout'] == 10


class TestFFmpegCommandBuilding:
    """Test FFmpeg command construction for caching"""
    
    def test_build_ffmpeg_command_with_downscale(self, cache_processor, cache_path):
        """Test FFmpeg command with downscaling enabled"""
        cmd = cache_processor._build_ffmpeg_command("concat.txt", cache_path, 960, 540)
        
        assert "ffmpeg" in cmd
        assert "-f" in cmd
        assert "concat" in cmd
        assert "-vf" in cmd
        assert "scale=960:540" in cmd
        assert "libx264" in cmd
        assert "aac" in cmd
        assert "-preset" in cmd
        assert cache_processor.settings.preset in cmd
    
    def test_build_ffmpeg_command_no_downscale(self, cache_path):
        """Test FFmpeg command without downscaling"""
        settings = CacheSettings(downscale_enabled=False)
        processor = CacheProcessor(settings)
        
        cmd = processor._build_ffmpeg_command("concat.txt", cache_path, 1920, 1080)
        
        # Should still apply scale filter to ensure consistency (always normalized)
        # Check that scale filter is in the command with original dimensions
        assert "-vf" in cmd
        scale_index = cmd.index("-vf") + 1
        assert "scale=1920:1080" in cmd[scale_index]
    
    def test_ffmpeg_command_includes_consistency_params(self, cache_processor, cache_path):
        """Test that command includes parameters for consistent output"""
        cmd = cache_processor._build_ffmpeg_command("concat.txt", cache_path, 960, 540)
        
        # Check for consistency parameters
        assert "-pix_fmt" in cmd
        assert "yuv420p" in cmd
        assert "-r" in cmd
        assert "30" in cmd
        assert "-b:a" in cmd
        assert "-ar" in cmd
        assert "48000" in cmd
        assert "-ac" in cmd
        assert "2" in cmd
        assert "-crf" in cmd
        assert "-movflags" in cmd
        assert "+faststart" in cmd
        assert "-max_muxing_queue_size" in cmd


class TestCacheCreation:
    """Test cache creation functionality"""
    
    def test_create_cache_no_videos(self, cache_processor):
        """Test cache creation with empty video list"""
        completion_callback = Mock()
        
        cache_processor.create_cache(
            video_paths=[],
            cache_path="cache_output",
            completion_callback=completion_callback
        )
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is False  # success = False
        assert "No videos" in args[1]
    
    def test_create_cache_creates_thread(self, cache_processor, sample_video_paths, cache_path):
        """Test that create_cache runs in background thread"""
        with patch('threading.Thread') as mock_thread:
            cache_processor.create_cache(
                video_paths=sample_video_paths,
                cache_path=cache_path
            )
            
            mock_thread.assert_called_once()
            thread_args = mock_thread.call_args
            assert thread_args[1]['target'] == cache_processor._cache_thread
    
    def test_cache_state_tracking(self, cache_processor, sample_video_paths, cache_path):
        """Test that caching state is tracked"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = []
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(cache_processor, '_get_video_dimensions', return_value=(1920, 1080)):
                with patch.object(cache_processor, '_get_total_duration', return_value=10.0):
                    assert cache_processor.is_caching is False
                    
                    cache_processor._cache_thread(
                        sample_video_paths,
                        cache_path,
                        None,
                        None
                    )
                    
                    assert cache_processor.is_caching is False  # Reset after completion


class TestCacheManagement:
    """Test cache file management"""
    
    def test_clear_cache_removes_old_files(self, cache_processor, tmp_path):
        """Test clearing old cache files"""
        old_cache = tmp_path / "old_cache.mp4"
        old_cache.touch()
        cache_processor.cached_files.append(str(old_cache))
        
        # Mock file age check to return old file
        with patch('os.path.getmtime') as mock_getmtime:
            with patch('os.path.exists', return_value=True):
                # Make file appear 25 hours old
                from datetime import datetime
                current_time = datetime.now().timestamp()
                mock_getmtime.return_value = current_time - (25 * 3600)
                
                cache_processor.clear_cache(max_age_hours=24)
        
        # File should be removed from tracked list
        assert str(old_cache) not in cache_processor.cached_files
    
    def test_clear_all_cache(self, cache_processor, tmp_path):
        """Test clearing all cache files"""
        cache1 = tmp_path / "cache1.mp4"
        cache2 = tmp_path / "cache2.mp4"
        cache1.touch()
        cache2.touch()
        
        cache_processor.cached_files = [str(cache1), str(cache2)]
        
        cache_processor.clear_all_cache()
        
        assert len(cache_processor.cached_files) == 0
    
    def test_cached_files_list_updated_on_success(self, cache_processor, sample_video_paths, cache_path):
        """Test that cached_files list is updated on successful cache"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = []
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(cache_processor, '_get_video_dimensions', return_value=(1920, 1080)):
                with patch.object(cache_processor, '_get_total_duration', return_value=10.0):
                    cache_processor._cache_thread(
                        sample_video_paths,
                        cache_path,
                        None,
                        None
                    )
        
        assert len(cache_processor.cached_files) > 0


class TestCacheCallbacks:
    """Test callback functionality in cache processor"""
    
    def test_progress_callback_during_caching(self, cache_processor, sample_video_paths, cache_path):
        """Test that progress callback is called"""
        progress_callback = Mock()
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = ["time=00:00:05.00 bitrate=1000kbits/s"]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(cache_processor, '_get_video_dimensions', return_value=(1920, 1080)):
                with patch.object(cache_processor, '_get_total_duration', return_value=10.0):
                    cache_processor._cache_thread(
                        sample_video_paths,
                        cache_path,
                        progress_callback,
                        None
                    )
        
        assert progress_callback.call_count > 0
    
    def test_completion_callback_on_success(self, cache_processor, sample_video_paths, cache_path):
        """Test completion callback on successful cache"""
        completion_callback = Mock()
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = []
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(cache_processor, '_get_video_dimensions', return_value=(1920, 1080)):
                with patch.object(cache_processor, '_get_total_duration', return_value=10.0):
                    cache_processor._cache_thread(
                        sample_video_paths,
                        cache_path,
                        None,
                        completion_callback
                    )
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is True  # success = True


class TestCancellation:
    """Test cache cancellation"""
    
    def test_cancel_caching(self, cache_processor):
        """Test canceling current cache operation"""
        mock_process = Mock()
        cache_processor.current_process = mock_process
        cache_processor.is_caching = True
        
        cache_processor.cancel_caching()
        
        mock_process.terminate.assert_called_once()
        assert cache_processor.is_caching is False
