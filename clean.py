import re
with open('Launcher/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    if '# credits to' in line.lower():
        new_lines.append(line)
        continue
    # Remove '(mirrors' to end of line or before closing parenthesis
    line = re.sub(r'\s*\(?mirrors [^)]+\)?', '', line, flags=re.IGNORECASE)
    line = re.sub(r'(?i)#\s*mirrors\s+dart.*', '', line)
    line = re.sub(r'(?i)mirrors dart.*', '', line)
    # common AI statements
    if 'This is a translation of the Dart code' in line: continue
    if 'The python equivalent of' in line: continue
    
    new_lines.append(line)

with open('Launcher/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
