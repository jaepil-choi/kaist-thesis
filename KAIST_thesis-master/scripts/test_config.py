"""
Test script to verify config.yaml loading

This script tests the configuration system and MongoDB connection.
"""

import sys
from pathlib import Path

# Add tnic to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tnic.config_loader import load_config, get_mongodb_config, get_tnic_config
from tnic.integrations import MongoDBAdapter


def test_config_loading():
    """Test configuration loading from config.yaml"""
    print("="*70)
    print("Testing Configuration Loading")
    print("="*70)
    
    try:
        # Load full config
        config = load_config()
        print("\n✅ Config loaded successfully!")
        
        # MongoDB config
        mongo_config = get_mongodb_config()
        print(f"\nMongoDB Configuration:")
        print(f"  Host: {mongo_config['host']}")
        print(f"  Database: {mongo_config['database']}")
        print(f"  Collection: {mongo_config['collection']}")
        
        # TNIC config
        tnic_config = get_tnic_config()
        print(f"\nTNIC Configuration:")
        print(f"  Language: {tnic_config['language']}")
        print(f"  Tokenizer: {tnic_config['korean_tokenizer']}")
        print(f"  Use frequency stopwords: {tnic_config['use_frequency_stopwords']}")
        print(f"  Median adjustment: {tnic_config['apply_median_adjustment']}")
        
        return True
    
    except FileNotFoundError as e:
        print(f"\n❌ Config file not found: {e}")
        print("\nTo fix:")
        print("  1. cd tnic")
        print("  2. cp config.example.yaml config.yaml")
        print("  3. Edit config.yaml with your settings")
        return False
    
    except Exception as e:
        print(f"\n❌ Error loading config: {e}")
        return False


def test_mongodb_connection():
    """Test MongoDB connection using config"""
    print("\n" + "="*70)
    print("Testing MongoDB Connection")
    print("="*70)
    
    try:
        # Create adapter from config
        adapter = MongoDBAdapter.from_config()
        print(f"\n✅ Connected to MongoDB!")
        print(f"  Database: {adapter.database_name}")
        print(f"  Collection: {adapter.collection_name}")
        
        # Get statistics
        try:
            stats = adapter.get_statistics()
            print(f"\nDatabase Statistics:")
            print(f"  Total documents: {stats['total_documents']:,}")
            print(f"  Number of years: {stats['n_years']}")
            print(f"  Years: {stats['years']}")
            print(f"  Number of firms: {stats['n_firms']:,}")
            print(f"  Total characters: {stats['total_characters']:,}")
            
            adapter.close()
            return True
        
        except Exception as e:
            print(f"\n⚠️  Connected but stats query failed: {e}")
            print("  (Database might be empty or have different schema)")
            adapter.close()
            return True
    
    except ConnectionError as e:
        print(f"\n❌ Failed to connect to MongoDB: {e}")
        print("\nTo fix:")
        print("  1. Make sure MongoDB is running")
        print("  2. Check connection string in config.yaml")
        print("  3. Verify database and collection names")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_query():
    """Test querying documents from MongoDB"""
    print("\n" + "="*70)
    print("Testing Query Functionality")
    print("="*70)
    
    try:
        adapter = MongoDBAdapter.from_config()
        
        # Try to get a few documents
        print("\nAttempting to query documents...")
        docs = adapter.get_documents()  # Get all documents (limited by MongoDB)
        
        if docs:
            print(f"✅ Successfully retrieved {len(docs)} documents")
            
            # Show first document structure
            if len(docs) > 0:
                print(f"\nFirst document fields:")
                for key in docs[0].keys():
                    print(f"  - {key}")
        else:
            print("⚠️  No documents found in collection")
            print("  Collection might be empty")
        
        adapter.close()
        return True
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "#"*70)
    print("# TNIC Configuration & MongoDB Connection Test")
    print("#"*70)
    
    results = []
    
    # Test 1: Config loading
    results.append(("Config Loading", test_config_loading()))
    
    # Test 2: MongoDB connection
    results.append(("MongoDB Connection", test_mongodb_connection()))
    
    # Test 3: Query
    results.append(("Query Functionality", test_query()))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Your configuration is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
