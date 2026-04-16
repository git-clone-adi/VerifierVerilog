# Strip markdown fences from mod.v
with open('mod.v', 'r') as f:
    content = f.read()

# Strip all markdown fences
content = content.replace('```verilog', '')
content = content.replace('```', '')
# Also strip any leading/trailing whitespace after removal
content = content.strip()

with open('mod.v', 'w') as f:
    f.write(content)

# Verify
with open('mod.v', 'r') as f:
    new_content = f.read()
    if '```' not in new_content:
        print('✅ Markdown fences removed from mod.v')
    else:
        print('❌ Fences still present')
