"""
Database migration utilities for the CSR Lambda API
Raw SQL implementation
"""
import logging
from typing import Dict, List, Any

from app.database import get_db_connection, execute_query, execute_update, execute_transaction

logger = logging.getLogger(__name__)


def create_tables():
    """
    Create all database tables using raw SQL
    """
    try:
        logger.info("Creating database tables...")
        
        # SQL statements to create tables
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cognito_user_id VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(100) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_cognito_user_id (cognito_user_id),
            INDEX idx_email (email),
            INDEX idx_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        create_user_profiles_table = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            avatar_url VARCHAR(500),
            bio TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        with get_db_connection() as connection:
            # Create tables
            execute_update(connection, create_users_table)
            execute_update(connection, create_user_profiles_table)
        
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    try:
        logger.warning("Dropping all database tables...")
        
        drop_statements = [
            "DROP TABLE IF EXISTS user_profiles",
            "DROP TABLE IF EXISTS users"
        ]
        
        with get_db_connection() as connection:
            for statement in drop_statements:
                execute_update(connection, statement)
        
        logger.warning("All database tables dropped")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise


def check_tables_exist() -> dict:
    """
    Check if required tables exist in the database
    """
    try:
        with get_db_connection() as connection:
            query = "SHOW TABLES"
            results = execute_query(connection, query)
            existing_tables = [list(row.values())[0] for row in results]
            
            required_tables = ['users', 'user_profiles']
            table_status = {}
            
            for table in required_tables:
                table_status[table] = table in existing_tables
            
            logger.info(f"Table status: {table_status}")
            return table_status
        
    except Exception as e:
        logger.error(f"Failed to check table existence: {str(e)}")
        raise


def get_table_info(table_name: str) -> dict:
    """
    Get detailed information about a specific table
    """
    try:
        with get_db_connection() as connection:
            # Check if table exists
            check_query = "SHOW TABLES LIKE %s"
            table_exists = execute_query(connection, check_query, (table_name,))
            
            if not table_exists:
                return {"exists": False}
            
            # Get column information
            columns_query = f"DESCRIBE {table_name}"
            columns_result = execute_query(connection, columns_query)
            
            columns = []
            for col in columns_result:
                columns.append({
                    "name": col["Field"],
                    "type": col["Type"],
                    "nullable": col["Null"] == "YES",
                    "default": col["Default"],
                    "primary_key": col["Key"] == "PRI"
                })
            
            # Get index information
            indexes_query = f"SHOW INDEX FROM {table_name}"
            indexes_result = execute_query(connection, indexes_query)
            
            indexes = {}
            for idx in indexes_result:
                idx_name = idx["Key_name"]
                if idx_name not in indexes:
                    indexes[idx_name] = {
                        "name": idx_name,
                        "columns": [],
                        "unique": idx["Non_unique"] == 0
                    }
                indexes[idx_name]["columns"].append(idx["Column_name"])
            
            # Get foreign key information (simplified)
            fk_query = f"""
            SELECT 
                CONSTRAINT_NAME as name,
                COLUMN_NAME as constrained_column,
                REFERENCED_TABLE_NAME as referred_table,
                REFERENCED_COLUMN_NAME as referred_column
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = %s 
            AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            fk_result = execute_query(connection, fk_query, (table_name,))
            
            foreign_keys = []
            for fk in fk_result:
                foreign_keys.append({
                    "name": fk["name"],
                    "constrained_columns": [fk["constrained_column"]],
                    "referred_table": fk["referred_table"],
                    "referred_columns": [fk["referred_column"]]
                })
            
            return {
                "exists": True,
                "columns": columns,
                "indexes": list(indexes.values()),
                "foreign_keys": foreign_keys
            }
        
    except Exception as e:
        logger.error(f"Failed to get table info for {table_name}: {str(e)}")
        raise


def run_migration_sql(sql_statements: list) -> bool:
    """
    Execute a list of SQL statements as a migration
    """
    try:
        with get_db_connection() as connection:
            for sql in sql_statements:
                logger.info(f"Executing SQL: {sql}")
                execute_update(connection, sql)
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


def initialize_database():
    """
    Initialize database with all required tables and initial data
    """
    try:
        logger.info("Initializing database...")
        
        # Check if tables already exist
        table_status = check_tables_exist()
        
        if all(table_status.values()):
            logger.info("All required tables already exist")
            return True
        
        # Create missing tables
        create_tables()
        
        # Verify tables were created
        table_status = check_tables_exist()
        if not all(table_status.values()):
            missing_tables = [table for table, exists in table_status.items() if not exists]
            raise Exception(f"Failed to create tables: {missing_tables}")
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


# Migration scripts for specific changes
MIGRATION_SCRIPTS = {
    "add_indexes_v1": [
        "CREATE INDEX IF NOT EXISTS idx_users_cognito_user_id ON users(cognito_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)"
    ],
    "add_constraints_v1": [
        "ALTER TABLE user_profiles ADD CONSTRAINT fk_user_profiles_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    ]
}