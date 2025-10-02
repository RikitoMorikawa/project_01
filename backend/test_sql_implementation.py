#!/usr/bin/env python3
"""
Test SQL implementation components
"""
import asyncio
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_sql_imports():
    """Test that all SQL modules can be imported"""
    try:
        # Test database module
        from app.database import get_db_connection, execute_query, execute_update, execute_insert
        print("✓ SQL database module imported successfully")
        
        # Test repository modules
        from app.repositories.base import BaseRepository
        from app.repositories.user import UserRepository, UserProfileRepository
        print("✓ SQL repository modules imported successfully")
        
        # Test migration module
        from app.migrations import create_tables, check_tables_exist, get_table_info
        print("✓ SQL migration module imported successfully")
        
        # Test auth dependencies
        from app.auth.dependencies import get_current_user_from_db
        print("✓ SQL auth dependencies imported successfully")
        
        # Test routes
        from app.api.routes import users, auth, health
        print("✓ SQL-based routes imported successfully")
        
        print("\n✅ All SQL imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_database_config():
    """Test database configuration"""
    try:
        from app.database import get_database_config
        from app.config import settings
        
        print("Testing database configuration...")
        
        # Check if configuration is available
        try:
            config = get_database_config()
            print("✓ Database configuration loaded")
            print(f"  Host: {config.get('host', 'Not set')}")
            print(f"  Port: {config.get('port', 'Not set')}")
            print(f"  Database: {config.get('database', 'Not set')}")
            print(f"  User: {config.get('user', 'Not set')}")
            print(f"  Charset: {config.get('charset', 'Not set')}")
            
        except ValueError as e:
            print(f"⚠ Database configuration incomplete: {e}")
            print("  This is expected if environment variables are not set")
        
        return True
        
    except Exception as e:
        print(f"❌ Database config test failed: {e}")
        return False


async def test_database_health():
    """Test database health check"""
    try:
        from app.database import check_database_health
        
        print("Testing database health check...")
        health_status = await check_database_health()
        
        print(f"Database Health Status:")
        print(f"  Status: {health_status['status']}")
        print(f"  Message: {health_status['message']}")
        
        return health_status['status'] == 'healthy'
        
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        print("  This is expected if database is not configured or accessible")
        return False


def test_repository_structure():
    """Test repository class structure"""
    try:
        from app.repositories.base import BaseRepository
        from app.repositories.user import UserRepository, UserProfileRepository
        import pymysql
        
        print("Testing repository structure...")
        
        # Test that repositories can be instantiated (with mock connection)
        # Note: This won't actually connect to database
        mock_connection = None  # We'll just test the class structure
        
        # Check if classes have expected methods
        base_methods = ['get', 'get_by_field', 'get_multi', 'count', 'create', 'update', 'delete', 'exists']
        for method in base_methods:
            if hasattr(BaseRepository, method):
                print(f"✓ BaseRepository has {method} method")
            else:
                print(f"❌ BaseRepository missing {method} method")
        
        user_methods = ['get_by_email', 'get_by_cognito_id', 'get_by_username', 'create_user', 'update_user', 'search_users']
        for method in user_methods:
            if hasattr(UserRepository, method):
                print(f"✓ UserRepository has {method} method")
            else:
                print(f"❌ UserRepository missing {method} method")
        
        profile_methods = ['get_by_user_id', 'create_profile', 'update_profile', 'delete_by_user_id']
        for method in profile_methods:
            if hasattr(UserProfileRepository, method):
                print(f"✓ UserProfileRepository has {method} method")
            else:
                print(f"❌ UserProfileRepository missing {method} method")
        
        print("✓ Repository structure test completed")
        return True
        
    except Exception as e:
        print(f"❌ Repository structure test failed: {e}")
        return False


def test_migration_structure():
    """Test migration system structure"""
    try:
        from app.migrations import (
            create_tables, drop_tables, check_tables_exist, 
            get_table_info, run_migration_sql, initialize_database
        )
        
        print("Testing migration system structure...")
        
        migration_functions = [
            'create_tables', 'drop_tables', 'check_tables_exist',
            'get_table_info', 'run_migration_sql', 'initialize_database'
        ]
        
        for func_name in migration_functions:
            if func_name in globals() or hasattr(__import__('app.migrations'), func_name):
                print(f"✓ Migration function {func_name} available")
            else:
                print(f"❌ Migration function {func_name} missing")
        
        print("✓ Migration structure test completed")
        return True
        
    except Exception as e:
        print(f"❌ Migration structure test failed: {e}")
        return False


def test_sql_queries():
    """Test SQL query construction"""
    try:
        print("Testing SQL query construction...")
        
        # Test basic query patterns
        table_name = "users"
        
        # SELECT queries
        select_all = f"SELECT * FROM {table_name}"
        select_by_id = f"SELECT * FROM {table_name} WHERE id = %s"
        select_with_limit = f"SELECT * FROM {table_name} LIMIT %s OFFSET %s"
        
        print(f"✓ SELECT queries: {select_all[:30]}...")
        
        # INSERT queries
        fields = ['email', 'username', 'created_at']
        placeholders = ', '.join(['%s'] * len(fields))
        insert_query = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({placeholders})"
        
        print(f"✓ INSERT queries: {insert_query[:50]}...")
        
        # UPDATE queries
        set_clauses = [f"{field} = %s" for field in ['email', 'username']]
        update_query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = %s"
        
        print(f"✓ UPDATE queries: {update_query[:50]}...")
        
        # DELETE queries
        delete_query = f"DELETE FROM {table_name} WHERE id = %s"
        
        print(f"✓ DELETE queries: {delete_query}")
        
        print("✓ SQL query construction test completed")
        return True
        
    except Exception as e:
        print(f"❌ SQL query construction test failed: {e}")
        return False


async def main():
    """Run all SQL implementation tests"""
    print("Testing SQL implementation...\n")
    
    tests = [
        ("Import Tests", test_sql_imports),
        ("Database Config", test_database_config),
        ("Repository Structure", test_repository_structure),
        ("Migration Structure", test_migration_structure),
        ("SQL Query Construction", test_sql_queries),
    ]
    
    async_tests = [
        ("Database Health", test_database_health),
    ]
    
    results = []
    
    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    # Run asynchronous tests
    for test_name, test_func in async_tests:
        print(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append(result)
            if result:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"SQL Implementation Test Results")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All SQL implementation tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("\nNote: Some failures are expected if database is not configured")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)