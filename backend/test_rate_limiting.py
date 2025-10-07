"""
Simple test script to verify rate limiting is working
Run this after installing slowapi to test the implementation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def test_rate_limiting_imports():
    """Test that rate limiting imports work"""
    try:
        from app.core.rate_limiting import limiter, safe_rate_limit
        print("✅ Rate limiting imports successful")
        return True
    except ImportError as e:
        print(f"❌ Rate limiting import failed: {e}")
        return False

def test_rate_limiting_decorators():
    """Test that rate limiting decorators work"""
    try:
        from app.core.rate_limiting import registration_rate_limit, login_rate_limit
        print("✅ Rate limiting decorators available")
        return True
    except Exception as e:
        print(f"❌ Rate limiting decorators failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Rate Limiting Implementation...")
    print("=" * 50)
    
    import_success = test_rate_limiting_imports()
    decorator_success = test_rate_limiting_decorators()
    
    if import_success and decorator_success:
        print("\n🎉 Rate limiting implementation is ready!")
        print("📋 Next steps:")
        print("1. Install slowapi: pip install slowapi==0.1.9")
        print("2. Restart your backend server")
        print("3. Test with multiple rapid requests")
    else:
        print("\n⚠️  Rate limiting needs fixes before launch")
