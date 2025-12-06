"""
Config Tab - Application settings and metadata templates
"""

import flet as ft
import json
import os
from pathlib import Path
from configs.config import Config
from access_control.session import session_manager


class ConfigTab:
    """Config tab for app settings and metadata templates"""
    
    def __init__(self, page):
        self.page = page
        
        # Metadata template fields
        self.template_name_field = None
        self.default_title_field = None
        self.default_description_field = None
        self.default_tags_field = None
        self.default_visibility_dropdown = None
        self.default_kids_checkbox = None
        
        # Settings fields
        self.output_directory_field = None
        self.ffmpeg_path_field = None
        
        # Templates storage
        self.templates_dir = Path("storage/data/templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Current template
        self.current_template = None
        self.templates_dropdown = None

        # helper for compatibility with different flet versions
        def make_option(key, text=None):
            try:
                if text is None:
                    return ft.dropdown.Option(key)
                return ft.dropdown.Option(key, text)
            except Exception:
                try:
                    if text is None:
                        return ft.DropdownOption(key)
                    return ft.DropdownOption(key, text)
                except Exception:
                    # Last resort: return a simple object that has 'key' attr
                    class _Opt:
                        def __init__(self, k, t=None):
                            self.key = k
                            self.text = t or k
                    return _Opt(key, text)

        self._make_option = make_option
        
    def build(self):
        """Build and return config tab layout"""
        
        # Metadata Templates Section
        templates_section = self._build_templates_section()
        
        # App Settings Section  
        settings_section = self._build_settings_section()
        
        # Account Info Section
        account_section = self._build_account_section()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Configuration", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                ft.Divider(),
                
                account_section,
                ft.Divider(),
                
                templates_section,
                ft.Divider(),
                
                settings_section,
                
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True
        )
    
    def _get_role_display_text(self, role: str) -> str:
        """Get user-friendly role display text"""
        role_lower = role.lower()
        if role_lower == 'free':
            return "Free tier user"
        elif role_lower == 'guest':
            return "Guest user"
        elif role_lower == 'premium':
            return "Premium user"
        elif role_lower == 'developer':
            return "Developer account"
        elif role_lower == 'administrator':
            return "Administrator account"
        else:
            return f"{role} user"
    
    def _build_account_section(self):
        """Build account information section with profile picture"""
        user_info = session_manager.get_user_display_info()
        user_name = user_info.get('name', 'Not logged in')
        user_email = user_info.get('email', '')
        user_role = user_info.get('role', 'None')
        user_picture = user_info.get('picture', '')
        
        # Create profile picture or icon
        if user_picture:
            profile_avatar = ft.CircleAvatar(
                foreground_image_src=user_picture,
                radius=30,
                bgcolor=ft.Colors.BLUE_700
            )
        else:
            profile_avatar = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=35, color=ft.Colors.WHITE),
                radius=30,
                bgcolor=ft.Colors.GREY_700
            )
        
        # Role permissions display
        permissions = []
        if session_manager.current_role:
            perms = session_manager.current_role.permissions
            # permissions may be a dict (older code) or a set/list of Permission enums
            if isinstance(perms, dict):
                permissions = list(perms.keys())
            else:
                try:
                    # iterate and get readable names
                    permissions = [getattr(p, 'value', str(p)) for p in perms]
                except Exception:
                    permissions = [str(perms)]

        permissions_text = ", ".join(permissions) if permissions else "No permissions"
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Account Information", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    profile_avatar,
                    ft.Column([
                        ft.Text(f"{user_name}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{user_email}", size=12, color=ft.Colors.GREY_400),
                        ft.Text(
                            self._get_role_display_text(user_role),
                            size=12,
                            color=ft.Colors.BLUE_400
                        ),
                        ft.Text(f"Permissions: {permissions_text}", size=10, color=ft.Colors.GREY_500),
                    ], spacing=2),
                ], spacing=15),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=8,
        )
    
    def _build_templates_section(self):
        """Build metadata templates section"""
        # Template selector
        # Dropdown options creation is delegated to _get_template_options which
        # uses a compatibility helper to construct Option objects for different
        # flet versions.
        self.templates_dropdown = ft.Dropdown(
            label="Select Template",
            options=self._get_template_options(),
            on_change=lambda e: self._on_template_selected(e),
            width=200,
        )
        
        # Template fields
        self.template_name_field = ft.TextField(
            label="Template Name",
            hint_text="e.g., Gaming Videos, Tutorials, etc."
        )
        
        self.default_title_field = ft.TextField(
            label="Default Title Template",
            hint_text="Use {filename} for auto-replacement",
            value="Merged Video - {filename}"
        )
        
        self.default_description_field = ft.TextField(
            label="Default Description",
            multiline=True,
            min_lines=3,
            max_lines=5,
            hint_text="Default video description...",
            value="Created with VideoMerger App\n\n#VideoMerger #MergedVideo"
        )
        
        self.default_tags_field = ft.TextField(
            label="Default Tags (comma separated)",
            hint_text="gaming, tutorial, merged, video",
            value="videomerger, merged, video"
        )
        
        self.default_visibility_dropdown = ft.Dropdown(
            label="Default Visibility",
            options=[
                ft.dropdown.Option("unlisted", "Unlisted"),
                ft.dropdown.Option("private", "Private"), 
                ft.dropdown.Option("public", "Public"),
            ],
            value="unlisted",
            width=150
        )
        
        self.default_kids_checkbox = ft.Checkbox(
            label="Made for kids by default",
            value=False
        )
        
        # Template buttons
        save_template_btn = ft.ElevatedButton(
            "Save Template",
            icon=ft.Icons.SAVE,
            on_click=self._save_template,
            bgcolor=ft.Colors.GREEN_700
        )
        
        load_template_btn = ft.ElevatedButton(
            "Load Template",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._load_template,
            bgcolor=ft.Colors.BLUE_700
        )
        
        delete_template_btn = ft.ElevatedButton(
            "Delete Template",
            icon=ft.Icons.DELETE,
            on_click=self._delete_template,
            bgcolor=ft.Colors.RED_700
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Metadata Templates", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Create reusable templates for video metadata", size=12, color=ft.Colors.GREY_400),
                
                ft.Row([self.templates_dropdown, load_template_btn], spacing=10),
                
                self.template_name_field,
                self.default_title_field,
                self.default_description_field,
                self.default_tags_field,
                
                ft.Row([
                    self.default_visibility_dropdown,
                    self.default_kids_checkbox
                ], spacing=20),
                
                ft.Row([
                    save_template_btn,
                    delete_template_btn,
                ], spacing=10),
                
            ], spacing=15),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=8,
        )
    
    def _build_settings_section(self):
        """Build app settings section"""
        # Output directory
        self.output_directory_field = ft.TextField(
            label="Default Output Directory",
            value=str(Path.home() / "Videos" / "VideoMerger"),
            expand=True,
            read_only=True
        )
        
        browse_output_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="Browse",
            on_click=self._browse_output_directory
        )
        
        # FFmpeg path (for advanced users)
        self.ffmpeg_path_field = ft.TextField(
            label="FFmpeg Path (optional)",
            hint_text="Leave empty to use system PATH",
            expand=True
        )
        
        browse_ffmpeg_btn = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip="Browse",
            on_click=self._browse_ffmpeg
        )
        
        # Test FFmpeg button
        test_ffmpeg_btn = ft.ElevatedButton(
            "Test FFmpeg",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._test_ffmpeg,
            bgcolor=ft.Colors.ORANGE_700
        )
        
        # Save settings button
        save_settings_btn = ft.ElevatedButton(
            "Save Settings",
            icon=ft.Icons.SETTINGS,
            on_click=self._save_settings,
            bgcolor=ft.Colors.GREEN_700
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Application Settings", size=18, weight=ft.FontWeight.BOLD),
                
                ft.Row([self.output_directory_field, browse_output_btn], spacing=5),
                ft.Row([self.ffmpeg_path_field, browse_ffmpeg_btn], spacing=5),
                
                ft.Row([test_ffmpeg_btn, save_settings_btn], spacing=10),
                
            ], spacing=15),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=8,
        )
    
    def _get_template_options(self):
        """Get available template options"""
        options = []
        try:
            for template_file in self.templates_dir.glob("*.json"):
                template_name = template_file.stem
                opt = self._make_option(template_name, template_name)
                options.append(opt)
        except:
            pass
        return options
    
    def _on_template_selected(self, e):
        """Handle template selection"""
        try:
            val = None
            if hasattr(e, 'control') and getattr(e.control, 'value', None) is not None:
                val = e.control.value
            elif hasattr(e, 'data'):
                val = e.data
            if val:
                self._load_template_by_name(val)
        except Exception as ex:
            print(f"_on_template_selected error: {ex}")
            self._show_error(f"Error selecting template: {ex}")
    
    def _save_template(self, e=None):
        """Save current template"""
        try:
            template_name = (self.template_name_field.value or "").strip()
            if not template_name:
                self._show_error("Please enter a template name")
                return

            template_data = {
                "name": template_name,
                "title": self.default_title_field.value,
                "description": self.default_description_field.value,
                "tags": self.default_tags_field.value,
                "visibility": self.default_visibility_dropdown.value,
                "made_for_kids": self.default_kids_checkbox.value,
            }

            try:
                template_path = self.templates_dir / f"{template_name}.json"
                with open(template_path, 'w') as f:
                    json.dump(template_data, f, indent=2)

                # Refresh dropdown
                self.templates_dropdown.options = self._get_template_options()
                # try to preserve selection
                self.templates_dropdown.value = template_name
                self.page.update()

                self._show_success(f"Template '{template_name}' saved successfully")

            except Exception as ex:
                self._show_error(f"Failed to save template: {str(ex)}")

        except Exception as ex:
            print(f"_save_template error: {ex}")
            self._show_error(f"Error saving template: {ex}")
    
    def _load_template(self, e=None):
        """Load template from file picker"""
        try:
            def handle_file_result(evt):
                try:
                    files = getattr(evt, 'files', None)
                    if files:
                        file_path = files[0].path if getattr(files[0], 'path', None) else files[0]
                        with open(file_path, 'r') as f:
                            template_data = json.load(f)
                        self._populate_template_fields(template_data)
                        self._show_success("Template loaded successfully")
                except Exception as ex:
                    print(f"handle_file_result error: {ex}")
                    self._show_error(f"Failed to load template: {ex}")

            file_picker = ft.FilePicker(on_result=handle_file_result)
            self.page.overlay.append(file_picker)
            self.page.update()
            file_picker.pick_files(
                dialog_title="Load Template",
                allowed_extensions=["json"],
                allow_multiple=False
            )
        except Exception as ex:
            print(f"_load_template error: {ex}")
            self._show_error(f"Error opening file picker: {ex}")
    
    def _load_template_by_name(self, template_name):
        """Load template by name from templates directory"""
        try:
            template_path = self.templates_dir / f"{template_name}.json"
            with open(template_path, 'r') as f:
                template_data = json.load(f)

            self._populate_template_fields(template_data)

        except Exception as ex:
            print(f"_load_template_by_name error: {ex}")
            self._show_error(f"Failed to load template: {str(ex)}")
    
    def _populate_template_fields(self, template_data):
        """Populate template fields with data"""
        try:
            self.template_name_field.value = template_data.get('name', '')
            self.default_title_field.value = template_data.get('title', '')
            self.default_description_field.value = template_data.get('description', '')
            self.default_tags_field.value = template_data.get('tags', '')
            # Some Dropdown option implementations use .value, others expect matching option objects
            try:
                self.default_visibility_dropdown.value = template_data.get('visibility', 'unlisted')
            except Exception:
                pass
            try:
                self.default_kids_checkbox.value = template_data.get('made_for_kids', False)
            except Exception:
                pass
            self.page.update()
        except Exception as ex:
            print(f"_populate_template_fields error: {ex}")
            self._show_error(f"Failed to populate template fields: {ex}")
    
    def _delete_template(self, e=None):
        """Delete selected template"""
        if not getattr(self.templates_dropdown, 'value', None):
            self._show_error("Please select a template to delete")
            return
        
        def confirm_delete(evt=None):
            dialog.open = False
            self.page.update()
            
            try:
                template_path = self.templates_dir / f"{self.templates_dropdown.value}.json"
                template_path.unlink()
                
                # Refresh dropdown and clear fields
                self.templates_dropdown.options = self._get_template_options()
                self.templates_dropdown.value = None
                self._clear_template_fields()
                self.page.update()
                
                self._show_success("Template deleted successfully")
                
            except Exception as ex:
                self._show_error(f"Failed to delete template: {str(ex)}")
        
        def cancel_delete(evt=None):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete '{self.templates_dropdown.value}' template?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete),
            ],
        )
        
        try:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        except Exception as ex:
            print(f"_delete_template dialog error: {ex}")
            self._show_error(f"Failed to show delete dialog: {ex}")
    
    def _clear_template_fields(self):
        """Clear all template fields"""
        self.template_name_field.value = ""
        self.default_title_field.value = "Merged Video - {filename}"
        self.default_description_field.value = "Created with VideoMerger App\n\n#VideoMerger #MergedVideo"
        self.default_tags_field.value = "videomerger, merged, video"
        self.default_visibility_dropdown.value = "unlisted"
        self.default_kids_checkbox.value = False

        try:
            self.page.update()
        except Exception:
            pass
    
    def _browse_output_directory(self, e):
        """Browse for output directory"""
        def handle_directory_result(e: ft.FilePickerResultEvent):
            if e.path:
                self.output_directory_field.value = e.path
                self.page.update()
        
        dir_picker = ft.FilePicker(on_result=handle_directory_result)
        self.page.overlay.append(dir_picker)
        self.page.update()
        dir_picker.get_directory_path(dialog_title="Select Output Directory")
    
    def _browse_ffmpeg(self, e):
        """Browse for FFmpeg executable"""
        def handle_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                self.ffmpeg_path_field.value = e.files[0].path
                self.page.update()
        
        file_picker = ft.FilePicker(on_result=handle_file_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            dialog_title="Select FFmpeg Executable",
            allowed_extensions=["exe"] if os.name == 'nt' else None,
            allow_multiple=False
        )
    
    def _test_ffmpeg(self, e):
        """Test FFmpeg installation"""
        import subprocess
        
        try:
            ffmpeg_cmd = self.ffmpeg_path_field.value.strip() or "ffmpeg"
            result = subprocess.run([ffmpeg_cmd, "-version"], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Extract version from output
                lines = result.stdout.split('\n')
                version_line = lines[0] if lines else "FFmpeg found"
                self._show_success(f"✓ {version_line}")
            else:
                self._show_error("FFmpeg test failed")
                
        except FileNotFoundError:
            self._show_error("FFmpeg not found. Please install FFmpeg or set correct path.")
        except subprocess.TimeoutExpired:
            self._show_error("FFmpeg test timed out")
        except Exception as ex:
            self._show_error(f"FFmpeg test error: {str(ex)}")
    
    def _save_settings(self, e):
        """Save application settings"""
        try:
            settings_data = {
                "output_directory": self.output_directory_field.value,
                "ffmpeg_path": self.ffmpeg_path_field.value.strip(),
            }
            
            settings_path = Path("storage/data/app_settings.json")
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w') as f:
                json.dump(settings_data, f, indent=2)
            
            self._show_success("Settings saved successfully")
            
        except Exception as ex:
            self._show_error(f"Failed to save settings: {str(ex)}")
    
    def _show_error(self, message: str):
        """Show error snackbar"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _show_success(self, message: str):
        """Show success snackbar"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.GREEN_700
            )
            self.page.snack_bar.open = True
            self.page.update()
