import os
from dotenv import load_dotenv
import urllib.parse
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    print("Testing MongoDB connection...")
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in environment variables.")
        return
    
    print(f"Original URI: {mongodb_uri}")
    
    # Parse and encode URI components
    if '@' in mongodb_uri:
        prefix = mongodb_uri.split('@')[0]
        suffix = mongodb_uri.split('@')[1]
        
        if '://' in prefix:
            protocol = prefix.split('://')[0]
            auth = prefix.split('://')[1]
            
            if ':' in auth:
                username = auth.split(':')[0]
                password = auth.split(':')[1]
                
                # Encode username and password
                encoded_username = urllib.parse.quote_plus(username)
                encoded_password = urllib.parse.quote_plus(password)
                
                # Reconstruct the URI with encoded components
                encoded_uri = f"{protocol}://{encoded_username}:{encoded_password}@{suffix}"
                print(f"Encoded URI: {encoded_uri}")
                
                try:
                    # Try to connect
                    client = MongoClient(encoded_uri, serverSelectionTimeoutMS=5000)
                    # Force a connection to verify it works
                    client.admin.command('ping')
                    print("SUCCESS: Connected to MongoDB!")
                    return
                except Exception as e:
                    print(f"ERROR: Failed to connect with encoded URI: {str(e)}")
    
    # Try with the original URI as fallback
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB with original URI!")
    except Exception as e:
        print(f"ERROR: Failed to connect with original URI: {str(e)}")

if __name__ == "__main__":
    test_mongodb_connection() 