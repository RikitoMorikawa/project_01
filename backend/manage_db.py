#!/usr/bin/env python3
"""
Database management CLI for the CSR Lambda API
"""
import argparse
import sys
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def init_db():
    """Initialize the database with all tables"""
    try:
        from app.migrations import initialize_database
        
        logger.info("Initializing database...")
        initialize_database()
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False


def create_tables():
    """Create all database tables"""
    try:
        from app.migrations import create_tables
        
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        return False


def drop_tables():
    """Drop all database tables"""
    try:
        from app.migrations import drop_tables
        
        # Confirmation prompt
        response = input("Are you sure you want to drop all tables? This will delete all data! (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            return False
        
        logger.warning("Dropping all database tables...")
        drop_tables()
        logger.warning("All tables dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        return False


def check_tables():
    """Check which tables exist in the database"""
    try:
        from app.migrations import check_tables_exist, get_table_info
        
        logger.info("Checking database tables...")
        table_status = check_tables_exist()
        
        print("\nTable Status:")
        print("-" * 40)
        for table, exists in table_status.items():
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{table:<20} {status}")
        
        # Show detailed info for existing tables
        print("\nTable Details:")
        print("-" * 40)
        for table, exists in table_status.items():
            if exists:
                info = get_table_info(table)
                print(f"\n{table.upper()}:")
                print(f"  Columns: {len(info['columns'])}")
                print(f"  Indexes: {len(info['indexes'])}")
                print(f"  Foreign Keys: {len(info['foreign_keys'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to check tables: {str(e)}")
        return False


def test_connection():
    """Test database connection"""
    try:
        from app.database import check_database_health
        import asyncio
        
        logger.info("Testing database connection...")
        
        # Run async function
        health_status = asyncio.run(check_database_health())
        
        print(f"\nDatabase Health Status:")
        print(f"Status: {health_status['status']}")
        print(f"Message: {health_status['message']}")
        
        return health_status['status'] == 'healthy'
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False


def show_config():
    """Show current database configuration"""
    try:
        from app.config import settings
        from app.database import get_database_url
        
        print("\nDatabase Configuration:")
        print("-" * 40)
        print(f"Environment: {settings.environment}")
        print(f"Host: {settings.db_host or 'Not set'}")
        print(f"Port: {settings.db_port}")
        print(f"Database: {settings.db_name or 'Not set'}")
        print(f"User: {settings.db_user or 'Not set'}")
        print(f"Region: {settings.aws_region}")
        
        # Show database URL (without password)
        try:
            db_url = get_database_url()
            # Mask password in URL
            if '@' in db_url:
                parts = db_url.split('@')
                if ':' in parts[0]:
                    user_pass = parts[0].split(':')
                    if len(user_pass) >= 3:  # mysql+pymysql://user:pass
                        masked_url = f"{':'.join(user_pass[:-1])}:***@{parts[1]}"
                        print(f"Database URL: {masked_url}")
                    else:
                        print(f"Database URL: {db_url}")
                else:
                    print(f"Database URL: {db_url}")
            else:
                print(f"Database URL: {db_url}")
        except Exception as e:
            print(f"Database URL: Error - {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to show config: {str(e)}")
        return False


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Database management CLI for CSR Lambda API")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database with all tables')
    
    # Create tables command
    subparsers.add_parser('create-tables', help='Create all database tables')
    
    # Drop tables command
    subparsers.add_parser('drop-tables', help='Drop all database tables (DANGEROUS!)')
    
    # Check tables command
    subparsers.add_parser('check-tables', help='Check which tables exist')
    
    # Test connection command
    subparsers.add_parser('test-connection', help='Test database connection')
    
    # Show config command
    subparsers.add_parser('show-config', help='Show database configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Command mapping
    commands = {
        'init': init_db,
        'create-tables': create_tables,
        'drop-tables': drop_tables,
        'check-tables': check_tables,
        'test-connection': test_connection,
        'show-config': show_config
    }
    
    command_func = commands.get(args.command)
    if not command_func:
        logger.error(f"Unknown command: {args.command}")
        return 1
    
    # Execute command
    success = command_func()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())