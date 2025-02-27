from app.db import VECTOR_IDX_PREFIX, VECTOR_IDX_NAME, get_redis
async def debug_vector_storage(rdb):
    """Debug function to check what's actually stored in Redis"""
    # 1. Check if any vectors exist at all
    all_keys = await rdb.keys(f"{VECTOR_IDX_PREFIX}*")
    print(f"Total vector keys found: {len(all_keys)}")
    
    if len(all_keys) > 0:
        # 2. Check the content of first few vectors
        for key in all_keys[:3]:  # Just check the first 3
            try:
                data = await rdb.json().get(key)
                print(f"\nKey: {key}")
                print(f"Has organization_id: {'organization_id' in data}")
                if 'organization_id' in data:
                    print(f"Organization ID: {data['organization_id']}")
                print(f"Chunk ID: {data.get('chunk_id', 'NOT FOUND')}")
                # Check if vector exists and its length
                has_vector = 'vector' in data
                vector_len = len(data['vector']) if has_vector else 0
                print(f"Has vector: {has_vector} (length: {vector_len})")
            except Exception as e:
                print(f"Error inspecting key {key}: {e}")
    
    # 3. Check index info
    try:
        index_info = await rdb.ft(VECTOR_IDX_NAME).info()
        print("\nIndex Info:")
        # Print important parts of index info
        fields_to_show = ['num_docs', 'index_definition', 'attributes']
        for field in fields_to_show:
            if field in index_info:
                print(f"  {field}: {index_info[field]}")
    except Exception as e:
        print(f"Error getting index info: {e}")

async def main():
    rdb = get_redis()
    await debug_vector_storage(rdb)

# Run the main function
import asyncio
asyncio.run(main())