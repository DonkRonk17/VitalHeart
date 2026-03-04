import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

sys.path.append(r'C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\Phase2')
from inferencepulse import UKEConnector, InferencePulseConfig

config = InferencePulseConfig({'uke': {'enabled': True, 'db_path': './nonexistent.db', 'fallback_log_path': './test_debug_fallback.jsonl', 'batch_size': 5}})
connector = UKEConnector(config)

print(f'Queue type: {type(connector.queue)}')
print(f'Queue length before: {len(connector.queue)}')

connector.index_event('test_event', {'value': 1}, ['test'])

print(f'Queue length after index: {len(connector.queue)}')

print('--- Calling _flush_to_uke() ---')
connector._flush_to_uke()

print(f'Queue length after flush: {len(connector.queue)}')

print(f'Fallback file exists: {os.path.exists("./test_debug_fallback.jsonl")}')
if os.path.exists('./test_debug_fallback.jsonl'):
    with open('./test_debug_fallback.jsonl', 'r') as f:
        print(f'Fallback content: {f.read()}')
else:
    print('Fallback file NOT created')
    print(f'Fallback path in connector: {connector.fallback_log_path}')
