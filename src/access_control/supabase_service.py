"""
Supabase Service
Handles metadata presets and other SQL-based data storage
"""

from supabase import create_client, Client
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class SupabaseService:
    """Supabase service for preset management and data storage"""
    
    def __init__(self, url: str = None, key: str = None):
        """Initialize Supabase client"""
        # Load from environment or config
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        self._client: Optional[Client] = None
        self._initialized = False
        
        if self.url and self.key:
            self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            self._client = create_client(self.url, self.key)
            self._initialized = True
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Supabase: {e}")
            self._initialized = False
    
    @property
    def client(self) -> Optional[Client]:
        """Get Supabase client"""
        return self._client
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase is properly initialized"""
        return self._initialized and self._client is not None
    
    # Preset Management Methods
    
    def create_preset(self, user_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new metadata preset"""
        if not self.is_available:
            raise Exception("Supabase not available")
        
        try:
            preset_doc = {
                'user_id': user_id,
                'name': preset_data.get('name'),
                'title': preset_data.get('title', ''),
                'description': preset_data.get('description', ''),
                'tags': preset_data.get('tags', ''),
                'visibility': preset_data.get('visibility', 'unlisted'),
                'made_for_kids': preset_data.get('made_for_kids', False),
                'metadata': preset_data.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }
            
            response = self._client.table('metadata_presets').insert(preset_doc).execute()
            return response.data[0] if response.data else preset_doc
        except Exception as e:
            print(f"Error creating preset: {e}")
            raise
    
    def get_user_presets(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all presets for a user"""
        if not self.is_available:
            return []
        
        try:
            response = self._client.table('metadata_presets').select(
                '*'
            ).eq('user_id', user_id).order('created_at', desc=True).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching presets: {e}")
            return []
    
    def get_preset(self, preset_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific preset by ID"""
        if not self.is_available:
            return None
        
        try:
            response = self._client.table('metadata_presets').select(
                '*'
            ).eq('id', preset_id).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching preset: {e}")
            return None
    
    def update_preset(self, preset_id: int, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a metadata preset"""
        if not self.is_available:
            raise Exception("Supabase not available")
        
        try:
            preset_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self._client.table('metadata_presets').update(
                preset_data
            ).eq('id', preset_id).execute()
            
            return response.data[0] if response.data else preset_data
        except Exception as e:
            print(f"Error updating preset: {e}")
            raise
    
    def delete_preset(self, preset_id: int) -> bool:
        """Delete a metadata preset"""
        if not self.is_available:
            return False
        
        try:
            self._client.table('metadata_presets').delete().eq('id', preset_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    
    def rename_preset(self, preset_id: int, new_name: str) -> bool:
        """Rename a preset"""
        if not self.is_available:
            return False
        
        try:
            self.update_preset(preset_id, {'name': new_name})
            return True
        except Exception as e:
            print(f"Error renaming preset: {e}")
            return False


# Singleton instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Get or create Supabase service singleton"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
