import urllib.request
import re

url_target = "https://raw.githubusercontent.com/babylife/China-ShangHai-IPTV-list/refs/heads/master/IPTV_Enhanced_change.m3u"
url_source = "https://raw.githubusercontent.com/ihipop/Shanghai-IPTV/refs/heads/master/tel_mu.m3u8"

target_data = urllib.request.urlopen(url_target).read().decode('utf-8').splitlines()
source_data = urllib.request.urlopen(url_source).read().decode('utf-8').splitlines()

def normalize_name(name):
    n = name.lower()
    for rm in [" ", "-", "hd", "「4k」", "「", "」", "上海", "频道", "卫视", "+"]:
        n = n.replace(rm, "")
    n2 = n.replace("4k", "").replace("cctv", "")
    if n2 != "":
        n = n2
    return n

source_channels = []
for line in source_data:
    if line.startswith("#EXTINF"):
        parts = line.split(",", 1)
        if len(parts) == 2:
            attrs = parts[0].replace("#EXTINF:-1", "").replace("#EXTINF: -1", "").strip()
            name = parts[1].strip()
            # extract tvg-name just in case
            m = re.search(r'tvg-name="([^"]+)"', attrs)
            tvg_name = m.group(1) if m else name
            source_channels.append({
                'attrs': attrs,
                'name': name,
                'tvg_name': tvg_name,
                'raw': line,
                'norm_name': normalize_name(name),
                'norm_tvg': normalize_name(tvg_name)
            })

new_lines = []
total_extinf = 0
updated_extinf = 0

for line in target_data:
    if line.startswith("#EXTM3U"):
        # Match url-tvg and x-tvg-url from source header
        source_header = source_data[0] if len(source_data) > 0 else ""
        
        # Build new header using source m3u x-tvg-url
        m_x_tvg = re.search(r'x-tvg-url="([^"]+)"', source_header)
        m_url_tvg = re.search(r'url-tvg="([^"]+)"', source_header)
        
        m_catchup = re.search(r'catchup="([^"]+)"', line)
        m_catchup_source = re.search(r'catchup-source="([^"]+)"', line)
        
        new_header = "#EXTM3U"
        if m_url_tvg:
            new_header += f' url-tvg="{m_url_tvg.group(1)}"'
        if m_x_tvg:
            new_header += f' x-tvg-url="{m_x_tvg.group(1)}"'
        if m_catchup:
            new_header += f' catchup="{m_catchup.group(1)}"'
        if m_catchup_source:
            new_header += f' catchup-source="{m_catchup_source.group(1)}"'
            
        new_lines.append(new_header)
    elif line.startswith("#EXTINF"):
        total_extinf += 1
        parts = line.split(",", 1)
        if len(parts) == 2:
            target_name = parts[1].strip()
            norm_target = normalize_name(target_name)
            
            # Find best match
            best_match = None
            
            # 1. Exact match on name
            for sc in source_channels:
                if sc['name'] == target_name or sc['tvg_name'] == target_name:
                    best_match = sc
                    break
            
            # 2. Normalize match
            if not best_match:
                for sc in source_channels:
                    if norm_target and sc['norm_name'] and norm_target == sc['norm_name']:
                        is_4k_target = '4k' in target_name.lower()
                        is_4k_source = '4k' in sc['name'].lower() or '4k' in sc['tvg_name'].lower()
                        if is_4k_target == is_4k_source:
                            best_match = sc
                            break
            
            # 3. Fallback partial match
            if not best_match:
                for sc in source_channels:
                    if norm_target and sc['norm_name'] and (norm_target in sc['norm_name'] or sc['norm_name'] in norm_target):
                        is_4k_target = '4k' in target_name.lower()
                        is_4k_source = '4k' in sc['name'].lower() or '4k' in sc['tvg_name'].lower()
                        if is_4k_target == is_4k_source:
                            best_match = sc
                            break
            
            if best_match:
                new_line = f'#EXTINF:-1 {best_match["attrs"]},{target_name}'
                new_lines.append(new_line)
                updated_extinf += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open("unicom.m3u8", "w") as f:
    f.write("\n".join(new_lines) + "\n")

print(f"Updated {updated_extinf} channels out of {total_extinf} EXTINF lines.")
