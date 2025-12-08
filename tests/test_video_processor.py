"""
Tests for Video Processor - FFmpeg video merging functionality
"""

import pytest
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.video_core.video_processor import VideoProcessor
from app.video_core.cache_processor import CacheSettings


@pytest.fixture
def video_processor():
    """Create a VideoProcessor instance for testing"""
    return VideoProcessor()


@pytest.fixture
def sample_video_paths(tmp_path):
    """Create sample video file paths for testing"""
    video1 = tmp_path / "video1.mp4"
    video2 = tmp_path / "video2.mp4"
    video3 = tmp_path / "video3.mp4"
    
    # Create empty files to simulate videos
    video1.touch()
    video2.touch()
    video3.touch()
    
    return [str(video1), str(video2), str(video3)]


@pytest.fixture
def output_path(tmp_path):
    """Create output path for testing"""
    return str(tmp_path / "output")


class TestFFmpegAvailability:
    """Test FFmpeg installation and availability"""
    
    def test_ffmpeg_installed(self, video_processor):
        """Test if FFmpeg is installed and accessible"""
        result = video_processor.check_ffmpeg()
        assert isinstance(result, bool)
    
    @patch('subprocess.run')
    def test_ffmpeg_not_found(self, mock_run, video_processor):
        """Test handling when FFmpeg is not installed"""
        mock_run.side_effect = FileNotFoundError()
        result = video_processor.check_ffmpeg()
        assert result is False
    
    @patch('subprocess.run')
    def test_ffmpeg_version_check(self, mock_run, video_processor):
        """Test FFmpeg version check command"""
        mock_run.return_value = Mock(returncode=0)
        video_processor.check_ffmpeg()
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args
        assert "-version" in args


class TestConcatFileCreation:
    """Test concat file creation for FFmpeg"""
    
    def test_concat_file_creation(self, video_processor, sample_video_paths):
        """Test that concat file is created correctly"""
        concat_file = video_processor._create_concat_file(sample_video_paths)
        
        assert os.path.exists(concat_file)
        
        with open(concat_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == len(sample_video_paths)
        
        for line, video_path in zip(lines, sample_video_paths):
            assert "file '" in line
            assert video_path.replace("\\", "/") in line.replace("\\", "/")
        
        # Cleanup
        if os.path.exists(concat_file):
            os.remove(concat_file)
    
    def test_concat_file_with_special_chars(self, video_processor, tmp_path):
        """Test concat file with special characters in paths"""
        special_path = tmp_path / "video with spaces & special.mp4"
        special_path.touch()
        
        concat_file = video_processor._create_concat_file([str(special_path)])
        
        with open(concat_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "file '" in content
        assert "video with spaces & special.mp4" in content.replace("\\", "/")
        
        # Cleanup
        if os.path.exists(concat_file):
            os.remove(concat_file)


class TestDurationCalculation:
    """Test video duration calculation"""
    
    @patch('subprocess.run')
    def test_get_total_duration_success(self, mock_run, video_processor, sample_video_paths):
        """Test successful duration calculation"""
        mock_run.return_value = Mock(stdout="10.5\n", returncode=0)
        
        total_duration = video_processor._get_total_duration(sample_video_paths)
        
        assert total_duration == 10.5 * len(sample_video_paths)
        assert mock_run.call_count == len(sample_video_paths)
    
    @patch('subprocess.run')
    def test_get_total_duration_failure(self, mock_run, video_processor, sample_video_paths):
        """Test handling when duration cannot be calculated"""
        mock_run.side_effect = Exception("FFprobe error")
        
        total_duration = video_processor._get_total_duration(sample_video_paths)
        
        assert total_duration is None
    
    @patch('subprocess.run')
    def test_ffprobe_command_format(self, mock_run, video_processor, sample_video_paths):
        """Test that ffprobe command is formatted correctly"""
        mock_run.return_value = Mock(stdout="10.0\n", returncode=0)
        
        video_processor._get_total_duration([sample_video_paths[0]])
        
        args = mock_run.call_args[0][0]
        assert "ffprobe" in args
        assert "-show_entries" in args
        assert "format=duration" in args


class TestTimeParsingFromFFmpeg:
    """Test parsing time from FFmpeg output"""
    
    def test_parse_time_hms_format(self, video_processor):
        """Test parsing HH:MM:SS.ms format"""
        line = "time=00:01:30.50 bitrate=1000.0kbits/s"
        result = video_processor._parse_time_from_ffmpeg(line)
        assert result == 90.5
    
    def test_parse_time_different_formats(self, video_processor):
        """Test parsing different time formats"""
        test_cases = [
            ("time=00:00:05.25 bitrate=", 5.25),
            ("time=01:30:45.00 bitrate=", 5445.0),
            ("time=00:10:00.50 bitrate=", 600.5),
        ]
        
        for line, expected in test_cases:
            result = video_processor._parse_time_from_ffmpeg(line)
            assert result == expected
    
    def test_parse_time_invalid_format(self, video_processor):
        """Test handling invalid time format"""
        invalid_lines = [
            "frame=100 fps=30",
            "Invalid line",
            "",
        ]
        
        for line in invalid_lines:
            result = video_processor._parse_time_from_ffmpeg(line)
            assert result is None


class TestVideoMerging:
    """Test video merging functionality"""
    
    def test_merge_videos_no_videos(self, video_processor):
        """Test merging with empty video list"""
        completion_callback = Mock()
        
        video_processor.merge_videos(
            video_paths=[],
            output_path="output.mp4",
            completion_callback=completion_callback
        )
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is False  # success = False
        assert "No videos" in args[1]
    
    def test_merge_videos_creates_thread(self, video_processor, sample_video_paths, output_path):
        """Test that merge_videos creates a background thread"""
        with patch('threading.Thread') as mock_thread:
            video_processor.merge_videos(
                video_paths=sample_video_paths,
                output_path=output_path
            )
            
            mock_thread.assert_called_once()
            thread_args = mock_thread.call_args
            assert thread_args[1]['target'] == video_processor._merge_videos_thread
    
    def test_codec_mapping(self, video_processor, sample_video_paths, output_path):
        """Test that codec names are properly mapped"""
        codec_tests = [
            ("H.264", "libx264"),
            ("H.265", "libx265"),
            ("VP9", "libvpx-vp9"),
            ("MPEG-4", "mpeg4"),
        ]
        
        for input_codec, expected_ffmpeg_codec in codec_tests:
            with patch('subprocess.Popen') as mock_popen:
                with patch.object(video_processor, '_create_concat_file', return_value='temp_concat.txt'):
                    with patch.object(video_processor, '_get_total_duration', return_value=10.0):
                        with patch('os.path.exists', return_value=True):
                            with patch('os.remove'):
                                mock_process = Mock()
                                mock_process.stderr = []
                                mock_process.returncode = 0
                                mock_process.wait = Mock()
                                mock_popen.return_value = mock_process
                                
                                video_processor._merge_videos_thread(
                                    sample_video_paths,
                                    output_path,
                                    input_codec,
                                    ".mp4",
                                    None,
                                    None
                                )
                                
                                # Check that FFmpeg was called with correct codec
                                assert mock_popen.called, "subprocess.Popen was not called"
                                call_args = mock_popen.call_args[0][0]
                                assert expected_ffmpeg_codec in call_args


class TestProcessControl:
    """Test process control functionality"""
    
    def test_cancel_processing(self, video_processor):
        """Test canceling current processing"""
        mock_process = Mock()
        video_processor.current_process = mock_process
        video_processor.is_processing = True
        
        video_processor.cancel_processing()
        
        mock_process.terminate.assert_called_once()
        assert video_processor.is_processing is False
    
    def test_processing_state_tracking(self, video_processor, sample_video_paths, output_path):
        """Test that processing state is tracked correctly"""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = []
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            assert video_processor.is_processing is False
            
            video_processor._merge_videos_thread(
                sample_video_paths,
                output_path,
                "H.264",
                ".mp4",
                None,
                None
            )
            
            assert video_processor.is_processing is False  # Should be reset after completion


class TestCallbacks:
    """Test callback functionality"""
    
    def test_progress_callback_called(self, video_processor, sample_video_paths, output_path):
        """Test that progress callback is called during merge"""
        progress_callback = Mock()
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = ["time=00:00:05.00 bitrate=1000kbits/s"]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(video_processor, '_get_total_duration', return_value=10.0):
                video_processor._merge_videos_thread(
                    sample_video_paths,
                    output_path,
                    "H.264",
                    ".mp4",
                    progress_callback,
                    None
                )
        
        assert progress_callback.call_count > 0
    
    def test_completion_callback_success(self, video_processor, sample_video_paths, output_path):
        """Test completion callback on successful merge"""
        completion_callback = Mock()
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = []
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            video_processor._merge_videos_thread(
                sample_video_paths,
                output_path,
                "H.264",
                ".mp4",
                None,
                completion_callback
            )
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is True  # success = True
    
    def test_completion_callback_failure(self, video_processor, sample_video_paths, output_path):
        """Test completion callback on failed merge"""
        completion_callback = Mock()
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stderr = []
            mock_process.returncode = 1  # Error code
            mock_popen.return_value = mock_process
            
            video_processor._merge_videos_thread(
                sample_video_paths,
                output_path,
                "H.264",
                ".mp4",
                None,
                completion_callback
            )
        
        completion_callback.assert_called_once()
        args = completion_callback.call_args[0]
        assert args[0] is False  # success = False


class TestCacheProcessor:
    """Test cache processor integration"""
    
    def test_merge_and_cache_delegates_to_cache_processor(self, video_processor, sample_video_paths):
        """Test that merge_and_cache delegates to cache processor"""
        cache_path = "test_cache"
        
        with patch.object(video_processor.cache_processor, 'create_cache') as mock_create_cache:
            video_processor.merge_and_cache(
                video_paths=sample_video_paths,
                cache_path=cache_path
            )
            
            mock_create_cache.assert_called_once()
            args = mock_create_cache.call_args[1]
            assert args['video_paths'] == sample_video_paths
            assert args['cache_path'] == cache_path
