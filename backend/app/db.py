# import json
# import numpy as np
# from redis.asyncio import Redis
# from redis.commands.search.field import TextField, VectorField, NumericField
# from redis.commands.search.indexDefinition import IndexDefinition, IndexType
# from redis.commands.search.query import Query
# from redis.commands.json.path import Path
# from app.config import settings

# VECTOR_IDX_NAME = 'idx:vector'
# VECTOR_IDX_PREFIX = 'vector:'
# CHAT_IDX_NAME = 'idx:chat'
# CHAT_IDX_PREFIX = 'chat:'

# def get_redis():
#     return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

# # VECTORS
# async def create_vector_index(rdb):
#     schema = (
#         TextField('$.chunk_id', no_stem=True, as_name='chunk_id'),
#         TextField('$.text', as_name='text'),
#         TextField('$.doc_name', as_name='doc_name'),
#         VectorField(
#             '$.vector',
#             'FLAT',
#             {
#                 'TYPE': 'FLOAT32',
#                 'DIM': settings.EMBEDDING_DIMENSIONS,
#                 'DISTANCE_METRIC': 'COSINE'
#             },
#             as_name='vector'
#         )
#     )
#     try:
#         await rdb.ft(VECTOR_IDX_NAME).create_index(
#             fields=schema,
#             definition=IndexDefinition(prefix=[VECTOR_IDX_PREFIX], index_type=IndexType.JSON)
#         )
#         print(f"Vector index '{VECTOR_IDX_NAME}' created successfully")
#     except Exception as e:
#         print(f"Error creating vector index '{VECTOR_IDX_NAME}': {e}")

# async def add_chunks_to_vector_db(rdb, chunks):
#     async with rdb.pipeline(transaction=True) as pipe:
#         for chunk in chunks:
#             pipe.json().set(VECTOR_IDX_PREFIX + chunk['chunk_id'], Path.root_path(), chunk)
#         await pipe.execute()

# async def search_vector_db(rdb, query_vector, top_k=settings.VECTOR_SEARCH_TOP_K):
#     query = (
#         Query(f'(*)=>[KNN {top_k} @vector $query_vector AS score]')
#         .sort_by('score')
#         .return_fields('score', 'chunk_id', 'text', 'doc_name')
#         .dialect(2)
#     )
#     res = await rdb.ft(VECTOR_IDX_NAME).search(query, {
#         'query_vector': np.array(query_vector, dtype=np.float32).tobytes()
#     })
#     return [{
#         'score': 1 - float(d.score),
#         'chunk_id': d.chunk_id,
#         'text': d.text,
#         'doc_name': d.doc_name
#     } for d in res.docs]

# async def get_all_vectors(rdb):
#     count = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, 0))
#     res = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, count.total))
#     return [json.loads(doc.json) for doc in res.docs]


# # CHATS
# async def create_chat_index(rdb):
#     try:
#         schema = (
#             NumericField('$.created', as_name='created', sortable=True),
#         )
#         await rdb.ft(CHAT_IDX_NAME).create_index(
#             fields=schema,
#             definition=IndexDefinition(prefix=[CHAT_IDX_PREFIX], index_type=IndexType.JSON)
#         )
#         print(f"Chat index '{CHAT_IDX_NAME}' created successfully")
#     except Exception as e:
#         print(f"Error creating chat index '{CHAT_IDX_NAME}': {e}")

# async def create_chat(rdb, chat_id, created):
#     chat = {'id': chat_id, 'created': created, 'messages': []}
#     await rdb.json().set(CHAT_IDX_PREFIX + chat_id, Path.root_path(), chat)
#     return chat

# async def add_chat_messages(rdb, chat_id, messages):
#     await rdb.json().arrappend(CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)

# async def chat_exists(rdb, chat_id):
#     return await rdb.exists(CHAT_IDX_PREFIX + chat_id)

# async def get_chat_messages(rdb, chat_id, last_n=None):
#     if last_n is None:
#         messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, '$.messages[*]')
#     else:
#         messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, f'$.messages[-{last_n}:]')
#     return [{'role': m['role'], 'content': m['content']} for m in messages] if messages else []

# async def get_chat(rdb, chat_id):
#     return await rdb.json().get(chat_id)

# async def get_all_chats(rdb):
#     q = Query('*').sort_by('created', asc=False)
#     count = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, 0))
#     res = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, count.total))
#     return [json.loads(doc.json) for doc in res.docs]


# # GENERAL
# async def setup_db(rdb):
#     # Create the vector index (deleting the existing one if present)
#     try:
#         await rdb.ft(VECTOR_IDX_NAME).dropindex(delete_documents=True)
#         print(f"Deleted vector index '{VECTOR_IDX_NAME}' and all associated documents")
#     except Exception as e:
#         pass
#     finally:
#         await create_vector_index(rdb)

#     # Make sure that the chat index exists, and create it if it doesn't
#     try:
#         await rdb.ft(CHAT_IDX_NAME).info()
#     except Exception:
#         await create_chat_index(rdb)

# async def clear_db(rdb):
#     for index_name in [VECTOR_IDX_NAME, CHAT_IDX_NAME]:
#         try:
#             await rdb.ft(index_name).dropindex(delete_documents=True)
#             print(f"Deleted index '{index_name}' and all associated documents")
#         except Exception as e:
#             print(f"Index '{index_name}': {e}")
import json
import numpy as np
from redis.asyncio import Redis
from redis.commands.search.field import TextField, VectorField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.commands.json.path import Path
from app.config import settings

VECTOR_IDX_NAME = 'idx:vector'
VECTOR_IDX_PREFIX = 'vector:'
CHAT_IDX_NAME = 'idx:chat'
CHAT_IDX_PREFIX = 'chat:'

def get_redis():
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

# VECTORS
async def create_vector_index(rdb):
    schema = (
        TextField('$.chunk_id', no_stem=True, as_name='chunk_id'),
        TextField('$.text', as_name='text'),
        TextField('$.doc_name', as_name='doc_name'),
        # Add organization_id as a TAG field for exact matching and efficient filtering
        TagField('$.organization_id', as_name='organization_id'),
        VectorField(
            '$.vector',
            'FLAT',
            {
                'TYPE': 'FLOAT32',
                'DIM': settings.EMBEDDING_DIMENSIONS,
                'DISTANCE_METRIC': 'COSINE'
            },
            as_name='vector'
        )
    )
    try:
        await rdb.ft(VECTOR_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[VECTOR_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Vector index '{VECTOR_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating vector index '{VECTOR_IDX_NAME}': {e}")

async def add_chunks_to_vector_db(rdb, chunks, organization_id):
    """Add chunks to vector DB with organization ID"""
    async with rdb.pipeline(transaction=True) as pipe:
        for chunk in chunks:
            # Add organization_id to each chunk
            chunk['organization_id'] = organization_id
            pipe.json().set(VECTOR_IDX_PREFIX + chunk['chunk_id'], Path.root_path(), chunk)
        await pipe.execute()

async def search_vector_db(rdb, query_vector, organization_id, top_k=settings.VECTOR_SEARCH_TOP_K):
    """Search vector DB with filtering by organization ID"""
    # Combining filters with KNN in a single query string
    # The correct syntax: "@tag_field:{value} =>[KNN $K @vector $BLOB AS score]"
    query_str = f"@organization_id:{{{organization_id}}} =>[KNN {top_k} @vector $query_vector AS score]"
    
    query = (
        Query(query_str)
        .sort_by('score')
        .return_fields('score', 'chunk_id', 'text', 'doc_name', 'organization_id')
        .dialect(2)
    )
    
    try:
        res = await rdb.ft(VECTOR_IDX_NAME).search(query, {
            'query_vector': np.array(query_vector, dtype=np.float32).tobytes()
        })
        
        # Add debug info if no results
        if len(res.docs) == 0:
            print(f"No results found for organization_id: {organization_id}")
            # Verify data exists for this organization
            count_query = Query(f"@organization_id:{{{organization_id}}}")
            count_result = await rdb.ft(VECTOR_IDX_NAME).search(count_query.paging(0, 0))
            print(f"Total vectors for organization {organization_id}: {count_result.total}")
        
        return [{
            'score': 1 - float(d.score),
            'chunk_id': d.chunk_id,
            'text': d.text,
            'doc_name': d.doc_name,
            'organization_id': d.organization_id
        } for d in res.docs]
        
    except Exception as e:
        print(f"Error searching vector DB: {e}")
        # Let's add a simple debug query to check syntax
        try:
            # Try a simple query without KNN to test if organization_id field works
            test_query = Query(f"@organization_id:{{{organization_id}}}")
            test_res = await rdb.ft(VECTOR_IDX_NAME).search(test_query.paging(0, 5))
            print(f"Basic filter test returned {len(test_res.docs)} documents")
        except Exception as e2:
            print(f"Error with basic filter query: {e2}")
        return []

async def get_all_vectors(rdb, organization_id=None):
    """Get all vectors, optionally filtered by organization_id"""
    if organization_id:
        query_str = f'@organization_id:{{{organization_id}}}'
    else:
        query_str = '*'
        
    count = await rdb.ft(VECTOR_IDX_NAME).search(Query(query_str).paging(0, 0))
    res = await rdb.ft(VECTOR_IDX_NAME).search(Query(query_str).paging(0, count.total))
    return [json.loads(doc.json) for doc in res.docs]


# CHATS
async def create_chat_index(rdb):
    try:
        schema = (
            NumericField('$.created', as_name='created', sortable=True),
            # Add organization_id to chat schema as well
            TagField('$.organization_id', as_name='organization_id'),
        )
        await rdb.ft(CHAT_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[CHAT_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Chat index '{CHAT_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating chat index '{CHAT_IDX_NAME}': {e}")

async def create_chat(rdb, chat_id, created, organization_id):
    chat = {
        'id': chat_id, 
        'created': created, 
        'organization_id': organization_id,
        'messages': []
    }
    await rdb.json().set(CHAT_IDX_PREFIX + chat_id, Path.root_path(), chat)
    return chat

async def add_chat_messages(rdb, chat_id, messages):
    await rdb.json().arrappend(CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)

async def chat_exists(rdb, chat_id):
    return await rdb.exists(CHAT_IDX_PREFIX + chat_id)

async def get_chat_messages(rdb, chat_id, last_n=None):
    if last_n is None:
        messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, '$.messages[*]')
    else:
        messages = await rdb.json().get(CHAT_IDX_PREFIX + chat_id, f'$.messages[-{last_n}:]')
    return [{'role': m['role'], 'content': m['content']} for m in messages] if messages else []

async def get_chat(rdb, chat_id):
    return await rdb.json().get(chat_id)

async def get_all_chats(rdb, organization_id=None):
    """Get all chats, optionally filtered by organization_id"""
    if organization_id:
        q = Query(f'@organization_id:{{{organization_id}}}').sort_by('created', asc=False)
    else:
        q = Query('*').sort_by('created', asc=False)
        
    count = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, 0))
    res = await rdb.ft(CHAT_IDX_NAME).search(q.paging(0, count.total))
    return [json.loads(doc.json) for doc in res.docs]

# ORGANIZATION MANAGEMENT
async def get_organization_stats(rdb, organization_id):
    """Get statistics about an organization's data"""
    # Count vectors
    vector_count = await rdb.ft(VECTOR_IDX_NAME).search(
        Query(f'@organization_id:{{{organization_id}}}').paging(0, 0)
    )
    
    # Count chats
    chat_count = await rdb.ft(CHAT_IDX_NAME).search(
        Query(f'@organization_id:{{{organization_id}}}').paging(0, 0)
    )
    
    return {
        'organization_id': organization_id,
        'vector_count': vector_count.total,
        'chat_count': chat_count.total
    }

async def list_organizations(rdb):
    """List all unique organization IDs in the system"""
    # For smaller datasets, we can aggregate the results manually
    # For larger datasets, you might want to maintain a separate set of organization IDs
    vector_orgs = set()
    chat_orgs = set()
    
    # Get all organization IDs from vectors
    vector_count = await rdb.ft(VECTOR_IDX_NAME).search(Query('*').paging(0, 0))
    if vector_count.total > 0:
        res = await rdb.ft(VECTOR_IDX_NAME).search(
            Query('*').return_fields('organization_id').paging(0, vector_count.total)
        )
        vector_orgs = {doc.organization_id for doc in res.docs}
    
    # Get all organization IDs from chats
    chat_count = await rdb.ft(CHAT_IDX_NAME).search(Query('*').paging(0, 0))
    if chat_count.total > 0:
        res = await rdb.ft(CHAT_IDX_NAME).search(
            Query('*').return_fields('organization_id').paging(0, chat_count.total)
        )
        chat_orgs = {doc.organization_id for doc in res.docs}
    
    # Combine the sets
    all_orgs = vector_orgs.union(chat_orgs)
    return sorted(list(all_orgs))


# GENERAL
async def setup_db(rdb):
    # Create the vector index (deleting the existing one if present)
    try:
        # await rdb.ft(VECTOR_IDX_NAME).dropindex(delete_documents=True)
        print(f"Deleted vector index '{VECTOR_IDX_NAME}' and all associated documents")
    except Exception as e:
        pass
    finally:
        await create_vector_index(rdb)

    # Make sure that the chat index exists, and create it if it doesn't
    try:
        await rdb.ft(CHAT_IDX_NAME).info()
    except Exception:
        await create_chat_index(rdb)

async def clear_db(rdb, organization_id=None):
    """Clear database, optionally only for a specific organization"""
    if organization_id:
        # Delete only the documents for the specified organization
        # Note: Redis doesn't support deleting documents by query directly
        # So we need to first get all matching docs and then delete them
        
        # Delete vectors for organization
        vector_query = Query(f'@organization_id:{{{organization_id}}}')
        vector_count = await rdb.ft(VECTOR_IDX_NAME).search(vector_query.paging(0, 0))
        if vector_count.total > 0:
            res = await rdb.ft(VECTOR_IDX_NAME).search(
                vector_query.return_fields('chunk_id').paging(0, vector_count.total)
            )
            keys = [VECTOR_IDX_PREFIX + doc.chunk_id for doc in res.docs]
            if keys:
                await rdb.delete(*keys)
            print(f"Deleted {len(keys)} vector documents for organization '{organization_id}'")
        
        # Delete chats for organization
        chat_query = Query(f'@organization_id:{{{organization_id}}}')
        chat_count = await rdb.ft(CHAT_IDX_NAME).search(chat_query.paging(0, 0))
        if chat_count.total > 0:
            res = await rdb.ft(CHAT_IDX_NAME).search(
                chat_query.return_fields('id').paging(0, chat_count.total)
            )
            keys = [CHAT_IDX_PREFIX + doc.id for doc in res.docs]
            if keys:
                await rdb.delete(*keys)
            print(f"Deleted {len(keys)} chat documents for organization '{organization_id}'")
    else:
        # Clear all data
        for index_name in [VECTOR_IDX_NAME, CHAT_IDX_NAME]:
            try:
                await rdb.ft(index_name).dropindex(delete_documents=True)
                print(f"Deleted index '{index_name}' and all associated documents")
            except Exception as e:
                print(f"Index '{index_name}': {e}")