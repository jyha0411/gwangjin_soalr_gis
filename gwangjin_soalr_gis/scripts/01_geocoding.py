import os
import pandas as pd

# 1. 파일 경로 설정
input_path = "data/raw/종합 운영 분류표.xlsx"
output_dir = "data/processed"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "solar_demand_points.csv")

# 2. 엑셀 불러오기
df_sites = pd.read_excel(input_path)
df_sites["운영유형"] = df_sites["최종 종합 유형"]

# 3. 광진구 18개 공공 시설별 실제 설치년도 딕셔너리 매칭
install_years = {
    "능동공영주차장": 2018,
    "긴고랑계곡화장실": 2019,
    "자양공공힐링센터": 2017,
    "중곡1동제2경로당": 2009,
    "자양3동주민센터": 2015,
    "중앙어린이집": 2012,
    "화양동주민센터": 2016,
    "중곡동다목적체육센터": 2014,
    "자양4빗물펌프장": 2013,
    "중곡4동주민센터": 2018,
    "중곡1동어린이집": 2010,
    "자양종합사회복지관": 2011,
    "광장제1경로당": 2012,
    "능동경로당": 2010,
    "광장제2경로당": 2021,
    "중곡종합사회복지관": 2009,
    "능동주민센터": 2013,
    "구의1동주민센터": 2015
}

df_sites["설치년도"] = df_sites["시설명"].map(install_years).fillna(2015).astype(int)

# 4. IEA PVPS 기반 연식별 중량 계수 & 개수 산출 함수
def calculate_waste_iea(row):
    kw = row["용량(kW)"]
    year = int(row["설치년도"])
    t = str(row["운영유형"])
    
    # Type C (용량 부족형) 및 Type D (고장·폐기형)만 폐기·교체 대상으로 가중치 산출
    if "Type D" in t or "Type C" in t:
        # A. 참고 지표: 예상 패널 개수 (1kW당 약 3장 가정)
        panels = int(round(kw * 3.0))
        
        # B. 핵심 지표: IEA PVPS 연식별 모듈 중량 계수 (kg/kW)
        if year <= 2000:
            kg_per_kw = 114.6
        elif year <= 2010:
            kg_per_kw = 88.7
        else: # 2011년 이후
            kg_per_kw = 73.3
            
        weight_kg = kw * kg_per_kw
        weight_ton = weight_kg / 1000.0
    else:
        panels = 0
        weight_kg = 0.0
        weight_ton = 0.0
        
    return pd.Series([panels, round(weight_kg, 2), round(weight_ton, 3)])

df_sites[["예상폐패널수(장)", "예상중량(kg)", "예상중량(ton)"]] = df_sites.apply(calculate_waste_iea, axis=1)

# 5. 백업 좌표 매칭
coords_backup = {
    "능동공영주차장": (37.55418, 127.08051),
    "긴고랑계곡화장실": (37.56091, 127.09881),
    "자양공공힐링센터": (37.53922, 127.06881),
    "중곡1동제2경로당": (37.56012, 127.08511),
    "자양3동주민센터": (37.53012, 127.07012),
    "중앙어린이집": (37.53697, 127.08432),
    "화양동주민센터": (37.54589, 127.07095),
    "중곡동다목적체육센터": (37.57218, 127.08638),
    "자양4빗물펌프장": (37.53281, 127.06584),
    "중곡4동주민센터": (37.55831, 127.09012),
    "중곡1동어린이집": (37.56491, 127.08272),
    "자양종합사회복지관": (37.53092, 127.07721),
    "광장제1경로당": (37.54712, 127.10212),
    "능동경로당": (37.55390, 127.08182),
    "광장제2경로당": (37.54891, 127.10451),
    "중곡종합사회복지관": (37.56832, 127.08845),
    "능동주민센터": (37.55418, 127.08051),
    "구의1동주민센터": (37.54391, 127.08691)
}

lats, lons = [], []
print("=== IEA PVPS 연식별 모듈 중량 계수 적용 매칭 시작 ===")
for idx, row in df_sites.iterrows():
    name = row["시설명"]
    lat, lon = coords_backup.get(name, (37.54, 127.08))
    lats.append(lat)
    lons.append(lon)
    print(f"[{idx+1}/18] {name} | 설치: {row['설치년도']}년 | 물량: {row['예상중량(kg)']} kg ({row['예상중량(ton)']} ton)")

df_sites["위도"] = lats
df_sites["경도"] = lons

# CSV 저장
df_sites.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n[성공] IEA 계수 적용 CSV 저장 완료: {output_path}")