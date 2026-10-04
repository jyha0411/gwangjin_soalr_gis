import os
import pandas as pd
import numpy as np
import folium

# 1. 데이터 불러오기
demand_path = "data/processed/solar_demand_points.csv"
if not os.path.exists(demand_path):
    print("오류: solar_demand_points.csv 파일이 없습니다. 01_geocoding.py를 먼저 실행하세요.")
    exit()

df = pd.read_csv(demand_path)

# Haversine 거리 계산 함수 (km 단위)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    return 2 * R * np.arcsin(np.sqrt(a))

demand_coords = df[["위도", "경도"]].values
weights_ton = df["예상중량(ton)"].values  # IEA 기반 중량 가중치

# =========================================================================
# [시나리오 A] 18개 공공시설 전체 대상 입지 분석 (이론적 최적지)
# =========================================================================
dist_matrix_18 = np.zeros((len(df), len(df)))
for i, d in enumerate(demand_coords):
    for j, c in enumerate(demand_coords):
        dist_matrix_18[i, j] = haversine(d[0], d[1], c[0], c[1])

weighted_dist_18 = []
for j in range(len(df)):
    weighted_dist_18.append(np.sum(dist_matrix_18[:, j] * weights_ton))

df_18 = df.copy()
df_18["총물류운송부하(km*ton)"] = weighted_dist_18
best_18_idx = np.argmin(weighted_dist_18)
best_18_site = df_18.iloc[best_18_idx]

# =========================================================================
# [시나리오 B] 공공 유휴부지 4곳 대상 입지 분석 (현실적 수거 거점)
# =========================================================================
candidates = [
    {"거점명": "능동공영주차장 부지", "위도": 37.55418, "경도": 127.08051},
    {"거점명": "광진구 자원순환센터 (차고지)", "위도": 37.56832, "경도": 127.08845},
    {"거점명": "중곡동 공영 유휴부지", "위도": 37.57218, "경도": 127.08638},
    {"거점명": "자양4빗물펌프장 부지", "위도": 37.53281, "경도": 127.06584}
]
df_cand = pd.DataFrame(candidates)
cand_coords = df_cand[["위도", "경도"]].values

dist_matrix_cand = np.zeros((len(df), len(df_cand)))
for i, d in enumerate(demand_coords):
    for j, c in enumerate(cand_coords):
        dist_matrix_cand[i, j] = haversine(d[0], d[1], c[0], c[1])

weighted_dist_cand = []
for j in range(len(df_cand)):
    weighted_dist_cand.append(np.sum(dist_matrix_cand[:, j] * weights_ton))

df_cand["총물류운송부하(km*ton)"] = weighted_dist_cand
best_cand_idx = np.argmin(weighted_dist_cand)
best_cand_site = df_cand.iloc[best_cand_idx]

os.makedirs("gis", exist_ok=True)

# =========================================================================
# 1. [시나리오 A 지도] 18개 시설 중심 이론적 최적지 시각화
# =========================================================================
map_a = folium.Map(
    location=[37.548, 127.082], zoom_start=13, max_zoom=18,
    tiles="https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png", attr="VWorld Base Map"
)

# 18개 수요점 표시
for idx, row in df_18.iterrows():
    w_ton = row["예상중량(ton)"]
    color = "red" if w_ton > 1.0 else ("orange" if w_ton > 0 else "navy")
    
    popup_html = f"""
    <div style="width: 250px; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; line-height: 1.6;">
        <h4 style="margin: 0 0 8px 0; color: #2C3E50; border-bottom: 2px solid #3498DB; padding-bottom: 4px;"><b>{row['시설명']}</b></h4>
        <b>운영유형:</b> {row['운영유형']}<br>
        <b>예상 중량:</b> <span style="color: #E74C3C; font-weight: bold;">{w_ton:.3f} ton</span> ({int(row['예상폐패널수(장)'])}장)<br>
        <b>총 물류운송부하:</b> <span style="color: #2980B9; font-weight: bold;">{row['총물류운송부하(km*ton)']:.3f} km·ton</span>
    </div>
    """
    folium.CircleMarker(
        location=[row["위도"], row["경도"]], radius=5 + (w_ton * 4), color=color,
        fill=True, fill_color=color, fill_opacity=0.7,
        popup=folium.Popup(popup_html, min_width=250, max_width=270)
    ).add_to(map_a)

# 이론적 최적지 (구의1동주민센터) 파란 핀
popup_a_best = f"""
<div style="width: 270px; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; line-height: 1.6;">
    <h4 style="margin: 0 0 8px 0; color: #2980B9; border-bottom: 2px solid #2980B9; padding-bottom: 4px;"><b>[이론적 최적지 1위] {best_18_site['시설명']}</b></h4>
    <b>운영유형:</b> {best_18_site['운영유형']}<br>
    <b>예상 중량:</b> <span style="color: #E74C3C; font-weight: bold;">{best_18_site['예상중량(ton)']:.3f} ton</span> ({int(best_18_site['예상폐패널수(장)'])}장 / 총 9.395 ton 수거 집하)<br>
    <b>총 물류운송부하:</b> <span style="color: #2980B9; font-weight: bold;">{best_18_site['총물류운송부하(km*ton)']:.3f} km·ton</span> (18개 시설 중 최소)
</div>
"""
folium.Marker(
    location=[best_18_site["위도"], best_18_site["경도"]],
    popup=folium.Popup(popup_a_best, min_width=270, max_width=290),
    icon=folium.Icon(color="blue", icon="info-sign")
).add_to(map_a)

# 수거 점선 연결 (구의1동주민센터로 집결)
for idx, row in df_18.iterrows():
    if row["예상중량(ton)"] > 0 and (row["위도"] != best_18_site["위도"] or row["경도"] != best_18_site["경도"]):
        folium.PolyLine(
            locations=[[row["위도"], row["경도"]], [best_18_site["위도"], best_18_site["경도"]]],
            color="#2B5B84", weight=2, opacity=0.5, dash_array="5, 5"
        ).add_to(map_a)

map_a.save("gis/gwangjin_scenario_a_map.html")
print("[성공] 시나리오 A 지도 저장 완료: gis/gwangjin_scenario_a_map.html")


# =========================================================================
# 2. [시나리오 B 지도] 4개 유휴부지 후보지 '비교 강조' 시각화
# =========================================================================
map_b = folium.Map(
    location=[37.548, 127.082], zoom_start=13, max_zoom=18,
    tiles="https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png", attr="VWorld Base Map"
)

# A. 배경 레이어: 18개 수요점 (가로 카드 형태로 팝업 규격 고정)
for idx, row in df_18.iterrows():
    w_ton = row["예상중량(ton)"]
    if w_ton > 0:
        demand_popup_html = f"""
        <div style="width: 230px; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; line-height: 1.6;">
            <h4 style="margin: 0 0 6px 0; color: #2C3E50; border-bottom: 2px solid #7F8C8D; padding-bottom: 4px;">
                <b>[폐패널 발생지] {row['시설명']}</b>
            </h4>
            <b>운영유형:</b> {row['운영유형']}<br>
            <b>발생 중량:</b> <span style="color: #E74C3C; font-weight: bold;">{w_ton:.3f} ton</span> ({int(row['예상폐패널수(장)'])}장)
        </div>
        """
        folium.CircleMarker(
            location=[row["위도"], row["경도"]], radius=5, color="#7F8C8D",
            fill=True, fill_color="#95A5A6", fill_opacity=0.8,
            popup=folium.Popup(demand_popup_html, min_width=230, max_width=250)
        ).add_to(map_b)

# B. 핵심 강조 레이어: 4개 공공 유휴부지 후보지 마커
min_load = best_cand_site["총물류운송부하(km*ton)"]

for idx, row in df_cand.iterrows():
    load = row["총물류운송부하(km*ton)"]
    is_best = (idx == best_cand_idx)
    
    if is_best:
        icon = folium.Icon(color="red", icon="star", prefix="fa")
        diff_str = "<b style='color: #C0392B;'>★ 최종 1위 선정 (최소 운송부하)</b>"
        border_color = "#C0392B"
    else:
        icon = folium.Icon(color="purple", icon="building", prefix="fa")
        diff_pct = ((load - min_load) / min_load) * 100
        diff_str = f"<b>운송부하 차이:</b> <span style='color: #E67E22; font-weight: bold;'>+{diff_pct:.1f}% 증가 (탈락)</span>"
        border_color = "#8E44AD"

    popup_cand_html = f"""
    <div style="width: 280px; font-family: 'Malgun Gothic', sans-serif; font-size: 13px; line-height: 1.6;">
        <h4 style="margin: 0 0 8px 0; color: {border_color}; border-bottom: 2px solid {border_color}; padding-bottom: 4px;">
            <b>{'[최적 거점 1위] ' if is_best else '[유휴부지 후보] '}{row['거점명']}</b>
        </h4>
        <b>운영유형:</b> Type A (공공 유휴부지 / 수거·차고지)<br>
        <b>자체 발생량:</b> 0.000 ton (태양광 미설치 부지)<br>
        <b>거점 적재용량:</b> <span style="color: #E74C3C; font-weight: bold;">총 9.395 ton 집하 가능</span><br>
        <b>총 물류운송부하:</b> <span style="color: {border_color}; font-weight: bold;">{load:.3f} km·ton</span><br>
        {diff_str}
    </div>
    """
    
    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=folium.Popup(popup_cand_html, min_width=280, max_width=300),
        icon=icon
    ).add_to(map_b)

# C. 1위 거점(능동공영주차장)으로 수거 경로 점선 연결
for idx, row in df_18.iterrows():
    if row["예상중량(ton)"] > 0:
        folium.PolyLine(
            locations=[[row["위도"], row["경도"]], [best_cand_site["위도"], best_cand_site["경도"]]],
            color="#C0392B", weight=2, opacity=0.6, dash_array="5, 5"
        ).add_to(map_b)

map_b.save("gis/gwangjin_scenario_b_map.html")
map_b.save("gis/gwangjin_depot_map.html")
print("[성공] 시나리오 B (팝업 규격 고정 완료) 지도 저장 완료: gis/gwangjin_scenario_b_map.html")