#!/usr/bin/env python3
"""
Quick test to verify the PostgreSQL connection string works
"""

import os
os.environ['DATABASE_URL'] = 'postgresql://parms2_db_user:spxgiscw2X69gXax4Wa1KksHutEUNiKi@dpg-d4gtodpr0fns739slra0-a/parms2_db'

try:
    import psycopg2
    
    # Test the connection
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    
    # Test a simple query
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    print("✅ Database connection successful!")
    print(f"PostgreSQL version: {db_version[0]}")
    
    cursor.close()
    conn.close()
    
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("This might be normal if connecting from outside Render's network")
