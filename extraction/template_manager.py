#!/usr/bin/env python3
"""
Template Manager for component-type-specific extraction templates.

This module handles:
- Template storage and retrieval
- Template matching for new product pages
- Template usage tracking
- Template statistics
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import re


class TemplateManager:
    """Manages extraction templates for different component types."""
    
    def __init__(self, db_connection_string: str):
        """
        Initialize TemplateManager with database connection.
        
        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.conn_string = db_connection_string
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.conn_string)
    
    def create_template(
        self,
        template_id: str,
        component_type: str,
        category: str,
        template_data: Dict,
        version: str = "1.0",
        created_by: str = "ai_agent",
        notes: Optional[str] = None
    ) -> bool:
        """
        Create a new extraction template.
        
        Args:
            template_id: Unique identifier for the template
            component_type: Type of component (e.g., "Gate Valve", "Resistor")
            category: Component category (e.g., "valve", "resistor", "capacitor")
            template_data: Template JSON structure
            version: Template version
            created_by: Who created the template
            notes: Optional notes about the template
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO extraction_templates 
                    (template_id, component_type, category, version, template_data, created_by, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (template_id) DO UPDATE SET
                        template_data = EXCLUDED.template_data,
                        version = EXCLUDED.version,
                        notes = EXCLUDED.notes
                """, (
                    template_id,
                    component_type,
                    category,
                    version,
                    json.dumps(template_data),
                    created_by,
                    notes
                ))
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"Error creating template: {e}")
            return False
        finally:
            conn.close()
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template data or None if not found
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM extraction_templates
                    WHERE template_id = %s AND is_active = true
                """, (template_id,))
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    result['template_data'] = json.loads(result['template_data']) if isinstance(result['template_data'], str) else result['template_data']
                    return result
                return None
        except Exception as e:
            print(f"Error getting template: {e}")
            return None
        finally:
            conn.close()
    
    def find_matching_template(
        self,
        page_title: str,
        page_url: str,
        html_content: str,
        component_type_hint: Optional[str] = None
    ) -> Optional[Tuple[str, Dict, float]]:
        """
        Find the best matching template for a product page.
        
        Args:
            page_title: Product page title
            page_url: Product page URL
            html_content: HTML content of the page
            component_type_hint: Optional hint about component type
            
        Returns:
            Tuple of (template_id, template_data, match_score) or None
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get all active templates
                cur.execute("""
                    SELECT template_id, component_type, category, template_data, success_rate, usage_count
                    FROM extraction_templates
                    WHERE is_active = true
                    ORDER BY success_rate DESC NULLS LAST, usage_count DESC
                """)
                templates = cur.fetchall()
                
                best_match = None
                best_score = 0.0
                
                for template_row in templates:
                    template_data = json.loads(template_row['template_data']) if isinstance(template_row['template_data'], str) else template_row['template_data']
                    page_patterns = template_data.get('pagePatterns', {})
                    
                    score = self._calculate_match_score(
                        page_title,
                        page_url,
                        html_content,
                        page_patterns,
                        template_row['component_type'],
                        component_type_hint
                    )
                    
                    # Boost score based on template success rate and usage
                    if template_row['success_rate']:
                        score *= (0.7 + 0.3 * float(template_row['success_rate']))
                    
                    if score > best_score:
                        best_score = score
                        best_match = (
                            template_row['template_id'],
                            template_data,
                            score
                        )
                
                # Only return if match score is above threshold
                if best_score >= 0.7:
                    return best_match
                return None
                
        except Exception as e:
            print(f"Error finding matching template: {e}")
            return None
        finally:
            conn.close()
    
    def _calculate_match_score(
        self,
        page_title: str,
        page_url: str,
        html_content: str,
        page_patterns: Dict,
        template_component_type: str,
        component_type_hint: Optional[str] = None
    ) -> float:
        """
        Calculate match score between page and template patterns.
        
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0
        
        # Check title keywords (weight: 0.3)
        title_keywords = page_patterns.get('titleKeywords', [])
        if title_keywords:
            max_score += 0.3
            title_lower = page_title.lower()
            matches = sum(1 for keyword in title_keywords if keyword.lower() in title_lower)
            if matches > 0:
                score += 0.3 * (matches / len(title_keywords))
        
        # Check URL patterns (weight: 0.2)
        url_patterns = page_patterns.get('urlPatterns', [])
        if url_patterns:
            max_score += 0.2
            url_lower = page_url.lower()
            matches = sum(1 for pattern in url_patterns if pattern.lower() in url_lower)
            if matches > 0:
                score += 0.2 * (matches / len(url_patterns))
        
        # Check HTML markers (weight: 0.3)
        html_markers = page_patterns.get('htmlMarkers', [])
        if html_markers:
            max_score += 0.3
            html_lower = html_content.lower()
            matches = sum(1 for marker in html_markers if marker.lower() in html_lower)
            if matches > 0:
                score += 0.3 * (matches / len(html_markers))
        
        # Check component type match (weight: 0.2)
        max_score += 0.2
        if component_type_hint:
            hint_lower = component_type_hint.lower()
            type_lower = template_component_type.lower()
            if hint_lower in type_lower or type_lower in hint_lower:
                score += 0.2
        
        # Normalize score
        if max_score > 0:
            return score / max_score
        return 0.0
    
    def log_template_usage(
        self,
        template_id: str,
        source_url: str,
        extraction_success: bool,
        extracted_fields_count: Optional[int] = None,
        missing_required_fields: Optional[List[str]] = None,
        extraction_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Log template usage for statistics tracking.
        
        Args:
            template_id: Template identifier
            source_url: URL that was extracted
            extraction_success: Whether extraction was successful
            extracted_fields_count: Number of fields successfully extracted
            missing_required_fields: List of missing required fields
            extraction_time_ms: Time taken for extraction
            error_message: Error message if extraction failed
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO template_usage_log
                    (template_id, source_url, extraction_success, extracted_fields_count,
                     missing_required_fields, extraction_time_ms, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    template_id,
                    source_url,
                    extraction_success,
                    extracted_fields_count,
                    missing_required_fields,
                    extraction_time_ms,
                    error_message
                ))
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"Error logging template usage: {e}")
            return False
        finally:
            conn.close()
    
    def get_template_statistics(self, template_id: str) -> Optional[Dict]:
        """
        Get statistics for a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Statistics dictionary or None
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM template_summary
                    WHERE template_id = %s
                """, (template_id,))
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            print(f"Error getting template statistics: {e}")
            return None
        finally:
            conn.close()
    
    def list_templates(
        self,
        category: Optional[str] = None,
        component_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict]:
        """
        List all templates with optional filters.
        
        Args:
            category: Filter by category
            component_type: Filter by component type
            active_only: Only return active templates
            
        Returns:
            List of template dictionaries
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM template_summary WHERE 1=1"
                params = []
                
                if active_only:
                    query += " AND is_active = true"
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                if component_type:
                    query += " AND component_type ILIKE %s"
                    params.append(f"%{component_type}%")
                
                query += " ORDER BY usage_count DESC, success_rate DESC NULLS LAST"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    # Parse JSONB if needed
                    if 'template_data' in result and isinstance(result['template_data'], str):
                        result['template_data'] = json.loads(result['template_data'])
                    results.append(result)
                
                return results
        except Exception as e:
            print(f"Error listing templates: {e}")
            return []
        finally:
            conn.close()

