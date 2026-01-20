import sqlite3
import json

conn = sqlite3.connect('ai_platform.db')
cursor = conn.cursor()

cursor.execute('SELECT name, mcp_endpoint, capabilities FROM marketplace_apps')
rows = cursor.fetchall()

for row in rows:
    print(f"App: {row[0]}")
    print(f"MCP Endpoint: {row[1]}")
    caps = row[2]
    if caps:
        try:
            caps_dict = json.loads(caps) if isinstance(caps, str) else caps
            tools = caps_dict.get('tools', [])
            print(f"Tools Count: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description', 'No description')[:50]}")
        except:
            print(f"Capabilities (raw): {caps}")
    else:
        print("Capabilities: None")
    print("---")

conn.close()
