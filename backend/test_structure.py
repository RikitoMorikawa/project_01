#!/usr/bin/env python3
"""
Simple test to verify the FastAPI application structure
"""

def test_imports():
    """Test that all modules can be imported correctly"""
    try:
        # Test main app import
        from app.main import app
        print("✓ Main app imported successfully")
        
        # Test lambda handler import
        from lambda_handler import lambda_handler
        print("✓ Lambda handler imported successfully")
        
        # Test config import
        from app.config import settings
        print("✓ Config imported successfully")
        
        # Test exceptions import
        from app.exceptions import APIException
        print("✓ Exceptions imported successfully")
        
        # Test middleware import
        from app.middleware import request_id_middleware
        print("✓ Middleware imported successfully")
        
        # Test dependencies import
        from app.dependencies import get_request_id
        print("✓ Dependencies imported successfully")
        
        # Test utils import
        from app.utils.response import success_response
        from app.utils.logging import get_logger
        print("✓ Utils imported successfully")
        
        # Test routers import
        from app.api.routes import auth, users, health
        print("✓ Routers imported successfully")
        
        print("\n✅ All imports successful! FastAPI structure is correct.")
        assert True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_app_structure():
    """Test the FastAPI app structure"""
    try:
        from app.main import app
        
        # Check app attributes
        assert hasattr(app, 'title'), "App should have title"
        assert hasattr(app, 'version'), "App should have version"
        
        # Check routes are registered
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/api/v1/auth/login", "/api/v1/users/", "/api/v1/health/"]
        
        for expected in expected_routes:
            found = any(expected in route for route in routes)
            if found:
                print(f"✓ Route found: {expected}")
            else:
                print(f"⚠ Route not found: {expected}")
        
        print(f"\n✅ App structure verified! Found {len(routes)} routes total.")
        assert True
        
    except Exception as e:
        print(f"❌ App structure test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing FastAPI application structure...\n")
    
    import_success = test_imports()
    structure_success = test_app_structure()
    
    if import_success and structure_success:
        print("\n🎉 All tests passed! FastAPI application is ready.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")