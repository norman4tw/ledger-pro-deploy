import gspread
from google.oauth2 import service_account
from google.auth import default
import os
from datetime import datetime

class GoogleSheetsService:
    def __init__(self, config):
        self.config = config
        self.client = None
        self.spreadsheet = None
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Try using service account credentials
            if self.config.get('GOOGLE_APPLICATION_CREDENTIALS'):
                # Use credentials file
                creds = service_account.Credentials.from_service_account_file(
                    self.config['GOOGLE_APPLICATION_CREDENTIALS'],
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                self.client = gspread.Client(auth=creds)
            elif self.config.get('GOOGLE_SERVICE_ACCOUNT_EMAIL') and self.config.get('GOOGLE_SHEETS_API_KEY'):
                # For development/testing - use API key method
                self.client = gspread
            else:
                raise Exception('No Google credentials configured')
            
            return True
        except Exception as e:
            print(f'Google Sheets auth error: {e}')
            return False
    
    def connect_spreadsheet(self, spreadsheet_url):
        """Connect to a spreadsheet by URL"""
        try:
            if not self.client:
                self.authenticate()
            
            # Extract spreadsheet ID from URL
            # Format: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
            spreadsheet_id = spreadsheet_url.split('/d/')[1].split('/')[0] if '/d/' in spreadsheet_url else spreadsheet_url
            
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            return True
        except Exception as e:
            print(f'Spreadsheet connection error: {e}')
            return False
    
    def get_sheet_data(self, sheet_name=None):
        """Get all data from a worksheet"""
        try:
            if not self.spreadsheet:
                return {'error': 'Not connected to spreadsheet'}
            
            if sheet_name:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            else:
                # Get first sheet
                worksheet = self.spreadsheet.sheet1
            
            data = worksheet.get_all_records()
            return {'data': data, 'headers': worksheet.row_values(1)}
        except Exception as e:
            return {'error': str(e)}
    
    def sync_gantt_data(self, spreadsheet_url):
        """
        Sync Gantt chart data from Google Sheets.
        Expected format: Phase Name, Start Date, End Date, Status, Progress
        """
        try:
            if not self.connect_spreadsheet(spreadsheet_url):
                return {'error': 'Failed to connect to spreadsheet'}
            
            data = self.get_sheet_data()
            if 'error' in data:
                return data
            
            records = data['data']
            headers = data['headers']
            
            # Parse records into project structure
            projects = {}
            for record in records:
                project_name = record.get('Project', record.get('project', 'Default'))
                
                if project_name not in projects:
                    projects[project_name] = {
                        'name': project_name,
                        'phases': [],
                        'tasks': []
                    }
                
                # Check if this is a phase or task row
                if record.get('Start Date') or record.get('Phase'):
                    phase = {
                        'name': record.get('Phase', record.get('phase', 'Untitled')),
                        'start_date': self._parse_date(record.get('Start Date', record.get('start_date'))),
                        'end_date': self._parse_date(record.get('End Date', record.get('end_date'))),
                        'status': record.get('Status', 'pending').lower(),
                        'progress': self._parse_progress(record.get('Progress', '0')),
                        'color': record.get('Color', '#002b59'),
                        'description': record.get('Description', '')
                    }
                    projects[project_name]['phases'].append(phase)
                
                # Check if this is a task
                if record.get('Task') or record.get('Title'):
                    task = {
                        'title': record.get('Task', record.get('title', 'Untitled')),
                        'assignee': record.get('Assignee', record.get('assignee', '')),
                        'due_date': self._parse_date(record.get('Due Date', record.get('due_date'))),
                        'status': record.get('Status', 'todo').lower(),
                        'priority': record.get('Priority', 'medium').lower(),
                        'deliverable_url': record.get('Deliverable URL', record.get('deliverable_url', '')),
                        'description': record.get('Description', '')
                    }
                    projects[project_name]['tasks'].append(task)
            
            return {'projects': list(projects.values()), 'synced_at': datetime.utcnow().isoformat()}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _parse_date(self, date_value):
        """Parse date from various formats"""
        if not date_value:
            return None
        
        if isinstance(date_value, str):
            # Try common formats
            formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt).date().isoformat()
                except ValueError:
                    continue
            return date_value  # Return as string if can't parse
        return date_value
    
    def _parse_progress(self, progress_value):
        """Parse progress percentage"""
        if not progress_value:
            return 0
        
        if isinstance(progress_value, (int, float)):
            return int(progress_value)
        
        progress_str = str(progress_value).replace('%', '').strip()
        try:
            return int(float(progress_str))
        except:
            return 0
    
    def verify_connection(self, spreadsheet_url):
        """Verify connection to a spreadsheet"""
        try:
            if not self.connect_spreadsheet(spreadsheet_url):
                return {'valid': False, 'error': 'Failed to connect'}
            
            # Try to get sheet info
            return {
                'valid': True,
                'title': self.spreadsheet.title,
                'sheets': [ws.title for ws in self.spreadsheet.worksheets()]
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
