#!/usr/bin/env python3
"""
Automated backup script for ClashArena database
"""

import os
import sys
import subprocess
import datetime
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

class DatabaseBackup:
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'clasharena')
        self.db_user = os.getenv('DB_USER', 'clasharena_user')
        self.db_password = os.getenv('DB_PASSWORD')
        self.backup_dir = os.getenv('BACKUP_DIR', './backups')
        self.s3_bucket = os.getenv('S3_BACKUP_BUCKET')
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """Create database backup"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"clasharena_backup_{timestamp}.sql"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_password
        
        try:
            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-f', backup_path,
                '--verbose',
                '--no-password'
            ]
            
            logging.info(f"Creating backup: {backup_filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"Backup created successfully: {backup_path}")
                
                # Compress backup
                compressed_path = self.compress_backup(backup_path)
                
                # Upload to S3 if configured
                if self.s3_bucket:
                    self.upload_to_s3(compressed_path)
                
                # Clean up old backups
                self.cleanup_old_backups()
                
                return compressed_path
            else:
                logging.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None

    def compress_backup(self, backup_path):
        """Compress backup file"""
        compressed_path = f"{backup_path}.gz"
        
        try:
            import gzip
            import shutil
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            os.remove(backup_path)
            
            logging.info(f"Backup compressed: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logging.error(f"Error compressing backup: {str(e)}")
            return backup_path

    def upload_to_s3(self, backup_path):
        """Upload backup to S3"""
        if not self.s3_bucket:
            return
        
        try:
            s3_client = boto3.client('s3')
            s3_key = f"backups/{os.path.basename(backup_path)}"
            
            logging.info(f"Uploading backup to S3: {self.s3_bucket}/{s3_key}")
            s3_client.upload_file(backup_path, self.s3_bucket, s3_key)
            
            logging.info("Backup uploaded to S3 successfully")
            
        except ClientError as e:
            logging.error(f"Error uploading to S3: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error uploading to S3: {str(e)}")

    def cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            import glob
            
            # Get all backup files
            backup_pattern = os.path.join(self.backup_dir, "clasharena_backup_*.sql.gz")
            backup_files = glob.glob(backup_pattern)
            
            # Sort by modification time
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # Keep only the most recent backups within retention period
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
            
            for backup_file in backup_files:
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(backup_file))
                
                if file_time < cutoff_date:
                    logging.info(f"Removing old backup: {backup_file}")
                    os.remove(backup_file)
                    
        except Exception as e:
            logging.error(f"Error cleaning up old backups: {str(e)}")

    def restore_backup(self, backup_path):
        """Restore database from backup"""
        if not os.path.exists(backup_path):
            logging.error(f"Backup file not found: {backup_path}")
            return False
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_password
        
        try:
            # Decompress if needed
            if backup_path.endswith('.gz'):
                import gzip
                import tempfile
                
                with gzip.open(backup_path, 'rb') as f_in:
                    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f_out:
                        f_out.write(f_in.read())
                        temp_path = f_out.name
            else:
                temp_path = backup_path
            
            # Restore database
            cmd = [
                'psql',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-f', temp_path,
                '--verbose',
                '--no-password'
            ]
            
            logging.info(f"Restoring backup: {backup_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Backup restored successfully")
                return True
            else:
                logging.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error restoring backup: {str(e)}")
            return False
        finally:
            # Clean up temp file if created
            if backup_path.endswith('.gz') and 'temp_path' in locals():
                os.unlink(temp_path)

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) < 3:
            print("Usage: python automated_backup.py restore <backup_file>")
            sys.exit(1)
        
        backup = DatabaseBackup()
        success = backup.restore_backup(sys.argv[2])
        sys.exit(0 if success else 1)
    else:
        # Create backup
        backup = DatabaseBackup()
        result = backup.create_backup()
        
        if result:
            print(f"Backup created successfully: {result}")
            sys.exit(0)
        else:
            print("Backup failed")
            sys.exit(1)

if __name__ == "__main__":
    main()
