"""
Config Tab - Application settings and metadata templates
Supports both authenticated (Google OAuth) and guest user instances
"""

import flet as ft
import json
import os
from pathlib import Path
from configs.config import Config
from access_control.session import session_manager
from access_control.roles import RoleType


class ConfigTab:
    """Config tab for app settings and metadata templates"""
    
    def __init__(self, page, on_logout_clicked=None, on_login_clicked=None):
        self.page = page
        self.on_logout_clicked = on_logout_clicked
        self.on_login_clicked = on_login_clicked
        
        # Detect if user is guest or authenticated
        self.is_guest = session_manager.is_guest
        self.admin_clicks = 0  # Counter for hidden admin button
        self.show_config_view = False  # Track whether to show config or admin dashboard
        
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
        """Build and return config tab layout based on user role"""
        from access_control.roles import Permission
        
        # Check if user has admin permission and should see admin dashboard
        if session_manager.has_permission(Permission.MANAGE_USERS.value):
            # Check if we should show config or admin dashboard
            if self.show_config_view:
                # Show config view with toggle button to go back to admin
                return self._build_authenticated_config_with_toggle()
            else:
                # Show admin dashboard
                return self._build_admin_dashboard()
        
        # Normal users see config based on their role
        if self.is_guest:
            return self._build_guest_config()
        else:
            return self._build_authenticated_config()
    
    def _build_authenticated_config(self):
        """Build config tab for authenticated (Google OAuth) users"""
        
        # Metadata Templates Section
        templates_section = self._build_templates_section()
        
        # App Settings Section  
        settings_section = self._build_settings_section()
        
        # Account Info Section
        account_section = self._build_account_section()
        
        # Hidden admin button container (click counter on title)
        title_container = ft.GestureDetector(
            content=ft.Text(
                "Configuration", 
                size=24, 
                weight=ft.FontWeight.BOLD, 
                color=ft.Colors.BLUE_400
            ),
            on_tap=self._handle_admin_click
        )
        
        return ft.Container(
            content=ft.Column([
                title_container,
                ft.Divider(),
                account_section,
                ft.Divider(),
                templates_section,
                ft.Divider(),
                settings_section,
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
            width=900,
            height=700
        )
    
    def _build_authenticated_config_with_toggle(self):
        """Build config tab for authenticated users with toggle back to admin dashboard"""
        from access_control.roles import Permission
        
        # Toggle button to switch back to admin dashboard
        toggle_button = ft.ElevatedButton(
            text="Back to Admin Dashboard",
            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            on_click=lambda e: self._toggle_admin_config_view(),
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
        )
        
        # Metadata Templates Section
        templates_section = self._build_templates_section()
        
        # App Settings Section  
        settings_section = self._build_settings_section()
        
        # Account Info Section
        account_section = self._build_account_section()
        
        # Hidden admin button container (click counter on title)
        title_container = ft.GestureDetector(
            content=ft.Text(
                "Configuration", 
                size=24, 
                weight=ft.FontWeight.BOLD, 
                color=ft.Colors.BLUE_400
            ),
            on_tap=self._handle_admin_click
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    title_container,
                    toggle_button,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                account_section,
                ft.Divider(),
                templates_section,
                ft.Divider(),
                settings_section,
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
            width=900,
            height=700
        )
    
    def _build_guest_config(self):
        """Build config tab for guest users (no YouTube access)"""
        
        user_info = session_manager.get_user_display_info()
        user_name = user_info.get('name', 'Guest User')
        
        # Google login suggestion
        login_suggestion = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.AMBER_700, size=32),
                ft.Text(
                    "Sign in with Google",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.AMBER_700
                ),
                ft.Text(
                    "Access metadata templates and upload your merged videos to YouTube",
                    size=12,
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                ),
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.15, "#FFA500"),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, "#FFA500")),
            alignment=ft.alignment.center,
        )
        
        # App Settings Section (still available for guests)
        settings_section = self._build_settings_section()
        
        # Guest account info
        account_section = ft.Container(
            content=ft.Column([
                ft.Text("Account Information", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=ft.Colors.GREY_700),
                    ft.Column([
                        ft.Text(f"Status: Guest", size=14, color=ft.Colors.GREY_400),
                        ft.Text(f"You can merge and save videos locally", size=12, color=ft.Colors.GREY_500),
                    ], spacing=2),
                ], spacing=10),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=8,
        )
        
        # Hidden admin button container on title
        title_container = ft.GestureDetector(
            content=ft.Text(
                "Configuration", 
                size=24, 
                weight=ft.FontWeight.BOLD, 
                color=ft.Colors.BLUE_400
            ),
            on_tap=self._handle_admin_click
        )
        
        return ft.Container(
            content=ft.Column([
                title_container,
                ft.Divider(),
                account_section,
                ft.Divider(),
                login_suggestion,
                ft.Divider(),
                settings_section,
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
            width=900,
            height=700
        )
    
    def _handle_admin_click(self, e):
        """Handle clicks on title for admin access (hidden button)"""
        self.admin_clicks += 1
        
        # Reset counter after 3 seconds of inactivity
        if self.admin_clicks == 1:
            def reset_counter():
                self.admin_clicks = 0
            self.page.run_task(lambda: __import__('asyncio').sleep(3) or reset_counter())
        
        # 5 quick clicks = admin access
        if self.admin_clicks >= 5:
            self.show_config_view = not getattr(self, 'show_config_view', False)
            # Trigger rebuild by creating a new dialog
            self._show_success("Toggled admin view. Close and reopen settings.")
    
    def _build_admin_dashboard(self):
        """Build the integrated admin dashboard"""
        from access_control.firebase_service import get_firebase_service
        from configs.config import Config
        
        # Initialize admin dashboard components if not already done
        if not hasattr(self, 'admin_users_table'):
            self.firebase_service = get_firebase_service()
            self.admin_users_data = []
            self.admin_filtered_users = []
        
        # Toggle button to switch to config view
        toggle_button = ft.ElevatedButton(
            text="Show Configuration",
            icon=ft.Icons.SETTINGS,
            on_click=lambda e: self._toggle_admin_config_view(),
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        )
        
        # Add/Update User Form
        self.admin_new_user_email = ft.TextField(
            label="Email address",
            hint_text="user@example.com",
            prefix_icon=ft.Icons.EMAIL,
            expand=True,
            width=300
        )
        
        self.admin_new_user_role = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("free", "Free"),
                ft.dropdown.Option("premium", "Premium"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value="free",
            width=150
        )
        
        add_user_button = ft.ElevatedButton(
            "Add/Update User",
            icon=ft.Icons.PERSON_ADD,
            on_click=self._admin_add_or_update_user,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
        )
        
        add_user_form = ft.Container(
            content=ft.Column([
                ft.Text("Add or Update User", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                ft.Text("Enter an email and role. If user exists, their role will be updated.", size=12, color=ft.Colors.GREY_400),
                ft.Row([
                    self.admin_new_user_email,
                    self.admin_new_user_role,
                    add_user_button
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREEN_700),
        )
        
        # Search and filter controls
        self.admin_search_field = ft.TextField(
            label="Search users (email, name)",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._admin_on_search_changed,
            expand=True
        )
        
        self.admin_filter_dropdown = ft.Dropdown(
            label="Filter by role",
            options=[
                ft.dropdown.Option("all", "All Roles"),
                ft.dropdown.Option("free", "Free"),
                ft.dropdown.Option("premium", "Premium"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value="all",
            on_change=self._admin_on_filter_changed,
            width=200
        )
        
        self.admin_refresh_button = ft.ElevatedButton(
            "Refresh",
            icon=ft.Icons.REFRESH,
            on_click=self._admin_refresh_users,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    ft.ControlState.HOVERED: ft.Colors.BLUE_600,
                },
            )
        )
        
        # Loading indicator - wrapped in container to prevent layout shift
        self.admin_loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)
        self.admin_loading_container = ft.Container(
            content=self.admin_loading_indicator,
            width=50,  # Fixed width to prevent shifting
            alignment=ft.alignment.center
        )
        
        # Users table header with fixed widths to match row layout
        table_header = ft.Container(
            content=ft.Row([
                ft.Container(width=50),  # Avatar space
                ft.Container(ft.Text("Email", weight=ft.FontWeight.BOLD, size=12), width=200),
                ft.Container(ft.Text("Name", weight=ft.FontWeight.BOLD, size=12), width=200),
                ft.Container(ft.Text("Role", weight=ft.FontWeight.BOLD, size=12), width=100),
                ft.Container(ft.Text("Last Login", weight=ft.FontWeight.BOLD, size=12), width=150),
                ft.Container(ft.Text("Status", weight=ft.FontWeight.BOLD, size=12), width=80),
                ft.Container(ft.Text("Actions", weight=ft.FontWeight.BOLD, size=12), width=150),
            ], spacing=10),
            padding=ft.padding.only(left=10, right=10)
        )
        
        # Users table content
        self.admin_users_table = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Load users on first build
        self._admin_load_users()
        
        # Main layout
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Admin Dashboard", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                    toggle_button,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text("User Management & Role Administration", size=14, color=ft.Colors.GREY_400),
                ft.Divider(),
                add_user_form,
                ft.Divider(),
                ft.Row([
                    self.admin_search_field,
                    self.admin_filter_dropdown,
                    self.admin_refresh_button,
                    self.admin_loading_container,
                ], spacing=10),
                ft.Divider(),
                table_header,
                ft.Divider(),
                self.admin_users_table,
            ], spacing=15, expand=True, scroll=ft.ScrollMode.AUTO),
            padding=20,
            expand=True,
            width=900,
            height=700
        )
    
    def _build_account_section(self):
        """Build account information section"""
        user_info = session_manager.get_user_display_info()
        user_name = user_info.get('name', 'Not logged in')
        user_role = user_info.get('role', 'None')
        user_picture_url = user_info.get('picture', '')
        is_guest = session_manager.is_guest
        
        # Profile image or icon
        if user_picture_url and not is_guest:
            # Authenticated user with profile picture
            profile_image = ft.CircleAvatar(
                foreground_image_src=user_picture_url,
                content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=28, color=ft.Colors.WHITE),  # Loading/fallback icon
                radius=24,
                bgcolor=ft.Colors.BLUE_700
            )
        else:
            # Guest user or no picture - use icon only for guests
            profile_image = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=28, color=ft.Colors.WHITE),
                radius=24,
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
                    profile_image,
                    ft.Column([
                        ft.Text(f"User: {user_name}", size=14),
                        ft.Text(f"{user_role} User", size=12, color=ft.Colors.GREY_400),
                        ft.Text(f"Permissions: {permissions_text}", size=10, color=ft.Colors.GREY_500),
                    ], spacing=2),
                ], spacing=10),
            ], spacing=10),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=8,
        )
    
    def _build_templates_section(self):
        """Build metadata templates section with presets"""
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
            "Save as Local Preset",
            icon=ft.Icons.SAVE,
            on_click=self._save_template,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
        )
        
        load_template_btn = ft.ElevatedButton(
            "Load Template",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._load_template,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE
        )
        
        delete_template_btn = ft.ElevatedButton(
            "Delete Template",
            icon=ft.Icons.DELETE,
            on_click=self._delete_template,
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE
        )
        
        # Database Preset buttons
        save_preset_btn = ft.ElevatedButton(
            "Save as Database Preset",
            icon=ft.Icons.CLOUD_UPLOAD,
            on_click=self._save_preset_to_database,
            bgcolor=ft.Colors.PURPLE_700,
            color=ft.Colors.WHITE
        )
        
        load_preset_btn = ft.ElevatedButton(
            "Load from Database",
            icon=ft.Icons.CLOUD_DOWNLOAD,
            on_click=self._load_presets_from_database,
            bgcolor=ft.Colors.PURPLE_700,
            color=ft.Colors.WHITE
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Metadata Templates & Presets", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Create reusable templates for video metadata", size=12, color=ft.Colors.GREY_400),
                
                # Local templates section
                ft.Text("Local Templates (JSON Files)", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
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
                
                ft.Divider(),
                
                # Database presets section
                ft.Text("Cloud Presets", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_300),
                ft.Text("Save your presets to the cloud for use across devices", size=10, color=ft.Colors.GREY_500),
                
                ft.Row([
                    save_preset_btn,
                    load_preset_btn,
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
            bgcolor=ft.Colors.ORANGE_700,
            color=ft.Colors.WHITE
        )
        
        # Save settings button
        save_settings_btn = ft.ElevatedButton(
            "Save Settings",
            icon=ft.Icons.SETTINGS,
            on_click=self._save_settings,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
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
    
    def _toggle_admin_config_view(self):
        """Toggle between admin dashboard and config view"""
        print("Toggled config/admin view")
        self.show_config_view = not self.show_config_view
        
        # Find and update the dialog content
        try:
            # Rebuild the entire view
            new_content = self.build()
            
            # Find the dialog in page.overlay and update its content
            for overlay_item in self.page.overlay:
                if isinstance(overlay_item, ft.AlertDialog) and overlay_item.open:
                    # Update dialog content with new build
                    overlay_item.content = new_content
                    self.page.update()
                    return
            
            # If no dialog found, just update the page
            self.page.update()
        except Exception as e:
            print(f"Error toggling view: {e}")
            self._show_error(f"Failed to toggle view: {str(e)}")
    
    def _admin_load_users(self):
        """Load all users from Firebase with security verification"""
        if hasattr(self, 'admin_loading_indicator') and self.admin_loading_indicator:
            self.admin_loading_indicator.visible = True
            try:
                self.page.update()
            except:
                pass
        
        try:
            if not hasattr(self, 'firebase_service'):
                from access_control.firebase_service import get_firebase_service
                self.firebase_service = get_firebase_service()
            
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Backend verification before loading users
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized admin access attempt by {current_user_email}")
                return
            
            self.admin_users_data = self.firebase_service.get_all_users()
            self.admin_filtered_users = self.admin_users_data.copy()
            self._admin_populate_users_table()
            
        except Exception as e:
            print(f"[ERROR] Failed to load users: {e}")
            self._show_error(f"Failed to load users: {str(e)}")
        finally:
            if hasattr(self, 'admin_loading_indicator') and self.admin_loading_indicator:
                self.admin_loading_indicator.visible = False
                try:
                    self.page.update()
                except:
                    pass
    
    def _admin_populate_users_table(self):
        """Populate the users table with data"""
        if not hasattr(self, 'admin_users_table') or not self.admin_users_table:
            return
        
        self.admin_users_table.controls.clear()
        
        if not self.admin_filtered_users:
            self.admin_users_table.controls.append(
                ft.Text("No users found", color=ft.Colors.GREY_400, italic=True)
            )
            self.page.update()
            return
        
        for user in self.admin_filtered_users:
            user_row = self._admin_create_user_row(user)
            self.admin_users_table.controls.append(user_row)
        
        self.page.update()
    
    def _admin_create_user_row(self, user):
        """Create a table row for a user"""
        from configs.config import Config
        from datetime import datetime
        
        email = user.get('email', 'N/A')
        name = user.get('name', 'N/A')
        role = user.get('role', 'unknown')
        last_login = user.get('last_login', 'Never')
        picture_url = user.get('picture', '')
        
        # Format last login
        if isinstance(last_login, datetime):
            last_login = last_login.strftime("%Y-%m-%d %H:%M")
        elif last_login and last_login != 'Never':
            try:
                from dateutil import parser
                last_login = parser.parse(last_login).strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        # Determine status
        status = user.get('disabled', False)
        status_text = "Disabled" if status else "Active"
        status_color = ft.Colors.RED_400 if status else ft.Colors.GREEN_400
        
        # Check if this is the super admin
        is_super_admin = (email == Config.SUPER_ADMIN_EMAIL)
        
        # Check if this is the current user (prevent self-editing)
        is_current_user = (email == session_manager.email)
        
        # Create user avatar with loading state
        if picture_url:
            user_avatar = ft.CircleAvatar(
                foreground_image_src=picture_url,
                content=ft.Icon(ft.Icons.PERSON, size=20),  # Fallback/loading icon
                radius=20,
            )
        else:
            user_avatar = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=20),
                bgcolor=ft.Colors.BLUE_GREY_700,
                radius=20,
            )
        
        # Action buttons
        role_button = ft.PopupMenuButton(
            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            tooltip="Change Role" if not (is_super_admin or is_current_user) else ("Super Admin - Role cannot be changed" if is_super_admin else "Cannot change your own role"),
            items=[
                ft.PopupMenuItem(text="Free", on_click=lambda e, u=user: self._admin_change_role(u, "free")),
                ft.PopupMenuItem(text="Premium", on_click=lambda e, u=user: self._admin_change_role(u, "premium")),
                ft.PopupMenuItem(text="Admin", on_click=lambda e, u=user: self._admin_change_role(u, "admin")),
            ],
            disabled=(is_super_admin or is_current_user)
        )
        
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_FOREVER,
            tooltip="Delete User" if not (is_super_admin or is_current_user) else ("Super Admin - Cannot be deleted" if is_super_admin else "Cannot delete your own account"),
            on_click=lambda e, u=user: self._admin_delete_user(u),
            disabled=(is_super_admin or is_current_user)
        )
        
        # Name display with super admin badge
        name_display = ft.Row([
            ft.Text(name, size=12),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SECURITY, size=12, color=ft.Colors.YELLOW_400),
                    ft.Text("SUPER ADMIN", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.YELLOW_400)
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.YELLOW_400),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=3,
                visible=is_super_admin
            )
        ], spacing=8, tight=True) if is_super_admin else ft.Text(name, size=12)
        
        return ft.Container(
            content=ft.Row([
                ft.Container(user_avatar, width=50),
                ft.Container(ft.Text(email, size=12, overflow=ft.TextOverflow.ELLIPSIS), width=200),
                ft.Container(name_display, width=200),
                ft.Container(
                    ft.Container(
                        content=ft.Text(role.title(), size=11, weight=ft.FontWeight.BOLD),
                        bgcolor=self._get_role_color(role),
                        padding=5,
                        border_radius=5,
                    ),
                    width=100
                ),
                ft.Container(ft.Text(str(last_login), size=11, color=ft.Colors.GREY_400, overflow=ft.TextOverflow.ELLIPSIS), width=150),
                ft.Container(ft.Text(status_text, size=11, color=status_color), width=80),
                ft.Container(ft.Row([role_button, delete_button], spacing=5), width=120),
            ], spacing=10),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_800 if not is_super_admin else ft.Colors.YELLOW_700),
            border_radius=5,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.YELLOW_400) if is_super_admin else None,
        )
    
    def _get_role_color(self, role: str) -> str:
        """Get background color for role badge"""
        colors = {
            'guest': ft.Colors.GREY_700,
            'free': ft.Colors.BLUE_700,
            'premium': ft.Colors.PURPLE_700,
            'admin': ft.Colors.RED_700,
        }
        return colors.get(role.lower(), ft.Colors.GREY_700)
    
    def _admin_change_role(self, user, new_role: str):
        """Change user role"""
        from configs.config import Config
        
        email = user.get('email')
        current_role = user.get('role')
        
        # Double-check: prevent self-editing
        if email == session_manager.email:
            self._show_error("Cannot change your own role")
            return
        
        if email == Config.SUPER_ADMIN_EMAIL:
            self._show_error("Cannot change super admin's role")
            return
        
        # Execute role change directly without confirmation
        self._admin_execute_role_change(email, new_role, current_role)
    
    def _admin_execute_role_change(self, email: str, new_role: str, old_role: str):
        """Execute the role change with security verification"""
        try:
            if not hasattr(self, 'firebase_service'):
                from access_control.firebase_service import get_firebase_service
                self.firebase_service = get_firebase_service()
            
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Verify admin permission before making changes
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized role change attempt by {current_user_email}")
                return
            
            # Security: Check rate limit
            if not self.firebase_service.check_rate_limit(current_user_email, 'role_change'):
                self._show_error("Rate limit exceeded. Please wait before making more changes.")
                return
            
            # Update role in Firebase
            success = self.firebase_service.update_user_role(email, new_role)
            
            # Log the admin action
            self.firebase_service.log_admin_action(
                admin_email=current_user_email,
                action='role_change',
                target_user=email,
                details={'old_role': old_role, 'new_role': new_role},
                success=success
            )
            
            if success:
                self._show_success(f"Role changed from '{old_role}' to '{new_role}' for {email}")
                self._admin_load_users()
            else:
                self._show_error("Failed to change role")
        
        except Exception as e:
            print(f"[ERROR] Role change failed: {e}")
            self._show_error(f"Failed to change role: {str(e)}")
    
    def _admin_delete_user(self, user):
        """Delete user directly"""
        email = user.get('email')
        
        # Double-check: prevent self-deletion
        if email == session_manager.email:
            self._show_error("Cannot delete your own account")
            return
        
        from configs.config import Config
        if email == Config.SUPER_ADMIN_EMAIL:
            self._show_error("Cannot delete super admin")
            return
        
        # Execute deletion directly without confirmation
        self._admin_execute_delete(email)
    
    def _admin_execute_delete(self, email: str):
        """Execute user deletion with security verification"""
        try:
            if not hasattr(self, 'firebase_service'):
                from access_control.firebase_service import get_firebase_service
                self.firebase_service = get_firebase_service()
            
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Verify admin permission
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized user deletion attempt by {current_user_email}")
                return
            
            # Security: Check rate limit
            if not self.firebase_service.check_rate_limit(current_user_email, 'user_deletion'):
                self._show_error("Rate limit exceeded. Please wait before making more changes.")
                return
            
            # Delete user
            success = self.firebase_service.delete_user(email)
            
            # Log the admin action
            self.firebase_service.log_admin_action(
                admin_email=current_user_email,
                action='user_deletion',
                target_user=email,
                details={},
                success=success
            )
            
            if success:
                self._show_success(f"Deleted user: {email}")
                self._admin_load_users()
            else:
                self._show_error(f"Failed to delete user: {email}")
        
        except Exception as e:
            print(f"[ERROR] User deletion failed: {e}")
            self._show_error(f"Delete failed: {str(e)}")
    
    def _admin_add_or_update_user(self, e):
        """Add or update a user"""
        if not hasattr(self, 'admin_new_user_email') or not self.admin_new_user_email:
            return
        
        email = self.admin_new_user_email.value.strip().lower()
        role = self.admin_new_user_role.value
        
        if not email:
            self._show_error("Email is required")
            return
        
        if "@" not in email or "." not in email.split("@")[-1]:
            self._show_error("Invalid email format")
            return
        
        from configs.config import Config
        if email == Config.SUPER_ADMIN_EMAIL and role != "admin":
            self._show_error("Super admin must have admin role")
            return
        
        try:
            if not hasattr(self, 'firebase_service'):
                from access_control.firebase_service import get_firebase_service
                self.firebase_service = get_firebase_service()
            
            if not self.firebase_service or not self.firebase_service.is_available:
                self._show_error("Firebase service unavailable")
                return
            
            # Security: Verify admin permission before making changes
            current_user_email = session_manager.email
            if not self.firebase_service.verify_admin_permission(current_user_email):
                self._show_error("Access denied: Admin verification failed")
                print(f"[SECURITY] Unauthorized user creation attempt by {current_user_email}")
                return
            
            # Security: Check rate limit
            if not self.firebase_service.check_rate_limit(current_user_email, 'user_creation'):
                self._show_error("Rate limit exceeded. Please wait before making more changes.")
                return
            
            # Check if user exists
            existing_user = self.firebase_service.get_user_by_email(email)
            
            if existing_user:
                # Update existing user
                success = self.firebase_service.update_user_role(email, role)
                
                # Log the admin action
                self.firebase_service.log_admin_action(
                    admin_email=current_user_email,
                    action='user_update',
                    target_user=email,
                    details={'new_role': role},
                    success=success
                )
                
                if success:
                    self._show_success(f"Updated {email} to {role} role")
                    self.admin_new_user_email.value = ""
                    self.page.update()
                    self._admin_load_users()
                else:
                    self._show_error("Failed to update user")
            else:
                # Create new user placeholder
                success = self.firebase_service.create_user_placeholder(email, role)
                
                # Log the admin action
                self.firebase_service.log_admin_action(
                    admin_email=current_user_email,
                    action='user_creation',
                    target_user=email,
                    details={'role': role},
                    success=success
                )
                
                if success:
                    self._show_success(f"Created user {email} with {role} role")
                    self.admin_new_user_email.value = ""
                    self.page.update()
                    self._admin_load_users()
                else:
                    self._show_error("Failed to create user")
        
        except Exception as ex:
            print(f"[ERROR] Add/update user failed: {ex}")
            self._show_error(f"Failed: {str(ex)}")
    
    def _admin_on_search_changed(self, e):
        """Filter users based on search query"""
        if not hasattr(self, 'admin_search_field') or not self.admin_search_field:
            return
        
        query = self.admin_search_field.value.lower().strip()
        
        if not query:
            self.admin_filtered_users = self.admin_users_data.copy()
        else:
            self.admin_filtered_users = [
                u for u in self.admin_users_data
                if query in u.get('email', '').lower() or query in u.get('name', '').lower()
            ]
        
        self._admin_populate_users_table()
    
    def _admin_on_filter_changed(self, e):
        """Filter users by role"""
        if not hasattr(self, 'admin_filter_dropdown') or not self.admin_filter_dropdown:
            return
        
        role_filter = self.admin_filter_dropdown.value
        
        if role_filter == "all":
            self.admin_filtered_users = self.admin_users_data.copy()
        else:
            self.admin_filtered_users = [
                u for u in self.admin_users_data
                if u.get('role', '').lower() == role_filter.lower()
            ]
        
        # Apply search filter if active
        if self.admin_search_field and self.admin_search_field.value:
            self._admin_on_search_changed(None)
        else:
            self._admin_populate_users_table()
    
    def _admin_refresh_users(self, e):
        """Refresh user list"""
        self._admin_load_users()
        self._show_success("Users refreshed")
    
    def _admin_view_analytics(self, e):
        """View analytics placeholder"""
        self._show_success("Analytics feature coming soon!")
    
    
    def _save_preset_to_database(self, e=None):
        """Save current template as a preset to Supabase database"""
        try:
            from access_control.supabase_service import get_supabase_service
            
            preset_name = (self.template_name_field.value or "").strip()
            if not preset_name:
                self._show_error("Please enter a preset name (e.g., Valorant, Lethal Company)")
                return
            
            supabase = get_supabase_service()
            if not supabase.is_available:
                self._show_error("Database connection not available. Check your Supabase configuration.")
                return
            
            user_id = session_manager.uid
            if not user_id:
                self._show_error("Cannot save preset: No user ID found")
                return
            
            preset_data = {
                "name": preset_name,
                "title": self.default_title_field.value or "",
                "description": self.default_description_field.value or "",
                "tags": self.default_tags_field.value or "",
                "visibility": self.default_visibility_dropdown.value or "unlisted",
                "made_for_kids": self.default_kids_checkbox.value or False,
                "metadata": {
                    "created_from": "config_tab",
                    "video_type": preset_name
                }
            }
            
            # Create preset
            result = supabase.create_preset(user_id, preset_data)
            self._show_success(f"Preset '{preset_name}' saved to cloud!")
            
        except Exception as ex:
            print(f"_save_preset_to_database error: {ex}")
            self._show_error(f"Failed to save preset: {str(ex)}")
    
    def _load_presets_from_database(self, e=None):
        """Load presets from Supabase database"""
        try:
            from access_control.supabase_service import get_supabase_service
            
            supabase = get_supabase_service()
            if not supabase.is_available:
                self._show_error("Database connection not available. Check your Supabase configuration.")
                return
            
            user_id = session_manager.uid
            if not user_id:
                self._show_error("Cannot load presets: No user ID found")
                return
            
            # Fetch presets from database
            presets = supabase.get_user_presets(user_id)
            if not presets:
                self._show_error("No cloud presets found. Create one first!")
                return
            
            # Show presets in a dialog
            self._show_presets_dialog(presets)
            
        except Exception as ex:
            print(f"_load_presets_from_database error: {ex}")
            self._show_error(f"Failed to load presets: {str(ex)}")
    
    def _show_presets_dialog(self, presets):
        """Show available presets in a dialog for selection"""
        def load_preset(preset):
            try:
                self.template_name_field.value = preset.get('name', '')
                self.default_title_field.value = preset.get('title', '')
                self.default_description_field.value = preset.get('description', '')
                self.default_tags_field.value = preset.get('tags', '')
                self.default_visibility_dropdown.value = preset.get('visibility', 'unlisted')
                self.default_kids_checkbox.value = preset.get('made_for_kids', False)
                self.page.update()
                
                dialog.open = False
                self.page.update()
                self._show_success(f"Preset '{preset.get('name')}' loaded!")
            except Exception as ex:
                self._show_error(f"Failed to load preset: {str(ex)}")
        
        def delete_preset(preset, dialog_ref):
            try:
                from access_control.supabase_service import get_supabase_service
                supabase = get_supabase_service()
                
                if supabase.delete_preset(preset.get('id')):
                    self._show_success(f"Preset '{preset.get('name')}' deleted!")
                    dialog_ref.open = False
                    self.page.update()
                else:
                    self._show_error("Failed to delete preset")
            except Exception as ex:
                self._show_error(f"Error deleting preset: {str(ex)}")
        
        # Create preset list
        preset_items = []
        for preset in presets:
            preset_name = preset.get('name', 'Unknown')
            preset_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(preset_name, size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(preset.get('tags', 'No tags'), size=10, color=ft.Colors.GREY_400),
                        ], spacing=2, expand=True),
                        ft.ElevatedButton(
                            "Load",
                            icon=ft.Icons.CHECK_CIRCLE,
                            on_click=lambda e, p=preset: load_preset(p),
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                            width=100,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, p=preset, d=None: delete_preset(p, dialog),
                            tooltip="Delete preset"
                        ),
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#555555")),
                )
            )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CLOUD_DOWNLOAD, color=ft.Colors.PURPLE_400),
                ft.Text(f"Your Cloud Presets ({len(presets)})", size=16)
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(
                    preset_items + [ft.Container(height=10)],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO
                ),
                width=600,
                height=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))
            ]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()