

import requests
import sys
import json

# Make sure this has /api/generate at the end
CLOUD_URL = "http://akrjc-34-16-168-144.a.free.pinggy.link/api/generate" 

try:
    with open(sys.argv[1], 'r') as f:
        verilog_code = f.read()

    # Use json.dumps to handle escaping automatically
    payload = {
        "model": "deepseek-coder-v2:16b",
        "prompt": f"Fix the errors in this Verilog code. Return ONLY the code:\n\n{verilog_code}",
        "stream": False
    }

    # Explicitly set headers and use 'json=' parameter
    headers = {"Content-Type": "application/json"}
    response = requests.post(
    CLOUD_URL, 
    json=payload, 
    allow_redirects=True, 
    timeout=300  # Give the GPU time to think!
)
    
    if response.status_code == 200:
        print(response.json().get('response'))
    else:
        print(f"Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"Local Error: {e}")