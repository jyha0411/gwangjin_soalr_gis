import os
import osmnx as ox

output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "gwangjin_roads.geojson")

print("=== OpenStreetMap 광진구 도로망 다운로드 및 데이터 변환 시작 ===")

# 1. 광진구 도로망 그래프 가져오기
G = ox.graph_from_place("Gwangjin-gu, Seoul, South Korea", network_type="drive")

# 2. GeoDataFrame 변환
nodes, edges = ox.graph_to_gdfs(G)

# 3. GeoJSON 저장 시 에러를 일으키는 '리스트 타입 속성'을 문자열로 변환 (에러 방지 핵심!)
for col in edges.columns:
    if col != 'geometry':
        edges[col] = edges[col].astype(str)

# 4. GeoJSON 저장
edges.to_file(output_file, driver="GeoJSON")

print(f"\n[성공] 도로망 데이터가 정상 저장되었습니다!")
print(f"저장 경로: {output_file} (총 도로 구간: {len(edges)}개)")