import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import calendar

st.set_page_config(page_title="讓我在台北上班好ㄇQQ", layout="wide")
st.title("讓我在台北上班好ㄇQQ")
st.markdown("比較三種票種（單程 / 回數 / 月票）的成本與回數票使用情況，Max關心您")

# -----------------基本票價設定-----------------
stations = ["南港", "台北", "板橋", "桃園"]
start_station = st.selectbox("選擇起站", stations)

single_ticket = {"南港": 320, "台北": 280, "板橋": 250, "桃園": 125}
multi_ticket = {"南港": 2620, "台北": 2295, "板橋": 2050, "桃園": 1025}  # 10趟
multi_ticket_count = 10
monthly_ticket = {"南港": 9405, "台北": 8230, "板橋": 7350, "桃園": 3675}

one_way_price = single_ticket[start_station]
round_trip_price = multi_ticket[start_station]
monthly_price = monthly_ticket[start_station]

# -----------------月份英文縮寫-----------------
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# -----------------台北上班日選擇-----------------
weekday_map = {"一":0, "二":1, "三":2, "四":3, "五":4}
taipei_workdays_str = st.multiselect("選擇台北上班日(國字)", ["一","二","三","四","五"], default=["一","二","三","四","五"])
taipei_workdays = [weekday_map[x] for x in taipei_workdays_str]

# -----------------年份選擇-----------------
year = st.number_input("選擇年度", min_value=2025, max_value=2030, value=2025)

# -----------------取得當月工作日-----------------
def get_workdays(year, month, workdays):
    _, last_day = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, last_day+1)
            if date(year, month, d).weekday() in workdays]

# -----------------計算台北/新竹工作日及需求趟數-----------------
taipei_days_list = []
all_weekdays_list = []
monthly_demand = {}
for m in range(1,13):
    all_weekdays = get_workdays(year, m, [0,1,2,3,4])
    taipei_days = get_workdays(year, m, taipei_workdays)
    hsinchu_days = len(all_weekdays) - len(taipei_days)
    monthly_demand[m] = hsinchu_days*2
    taipei_days_list.append(len(taipei_days))
    all_weekdays_list.append(len(all_weekdays))

# -----------------年度票價計算-----------------
total_cost = 0
recommend_type = []
avg_price_list = []
topup_list = []
leftover_list = []

previous_left = 0

for i in range(1,13):
    demand = monthly_demand[i]
    net_demand = max(0, demand - previous_left)

    if net_demand > 0:
        topup_sets = (net_demand + multi_ticket_count -1)//multi_ticket_count
        cost_m = topup_sets * round_trip_price
    else:
        topup_sets = 0
        cost_m = 0

    cost_s = demand * one_way_price
    cost_mo = monthly_price
    costs = {"單程票": cost_s, "回數票": cost_m, "月票": cost_mo}

    if net_demand == 0:
        rec = "無需求"
        avg_price = 0
        topup = 0
        leftover = 0
    else:
        rec = min(costs, key=costs.get)
        if rec == "單程票":
            avg_price = one_way_price
            topup = 0
            leftover = 0
        elif rec == "月票":
            avg_price = round(cost_mo / demand)  # 四捨五入
            topup = 0
            leftover = 0
        else:
            avg_price = round(cost_m / net_demand)  # 四捨五入
            topup = topup_sets
            leftover = previous_left + topup_sets*multi_ticket_count - net_demand

    if rec == "回數票":
        previous_left = leftover
    else:
        previous_left = 0

    total_cost += costs[rec] if rec != "無需求" else 0
    recommend_type.append(rec)
    avg_price_list.append(avg_price)
    topup_list.append(topup)
    leftover_list.append(leftover)

# -----------------highlight 樣式切換-----------------
highlight_style = st.radio(
    "選擇 Highlight 樣式",
    ["亮色主題（黃底黑字）", "深色主題（綠底白字）"],
    horizontal=True
)

def highlight_min(s):
    is_min = s == s.min()
    if highlight_style == "亮色主題（黃底黑字）":
        return ['background-color: yellow; color: black; font-weight: bold;' if v else '' for v in is_min]
    else:
        return ['background-color: #2e7d32; color: white; font-weight: bold;' if v else '' for v in is_min]

# -----------------通用表格樣式（固定第一欄寬度）-----------------
common_styles = [
    {'selector': 'th.col0', 'props': [('min-width', '120px'), ('max-width', '120px')]}
]

# -----------------基本票價表-----------------
st.subheader("基本票價參考")
df_basic = pd.DataFrame({
    "票種": ["單程票","回數票(10趟)","月票"],
    "單價": [
        f"{one_way_price:,}",
        f"{round_trip_price:,} (固定10趟套票)",
        f"{monthly_price:,}"
    ]
})
styled_basic = df_basic.style.set_table_styles(common_styles).hide(axis="index")
st.dataframe(styled_basic, width='stretch')

# -----------------年度票價明細-----------------
st.subheader(f"{year}年度票價明細與回數票使用情況 (當年度交通成本: {total_cost:,})")
df_overview = pd.DataFrame({
    "票種": [
        "單程票",
        "回數票",
        "月票",
        "推薦票種",
        "推薦票種平均單價",
        "Top-up 次數",
        "當月需求趟數",
        "當月剩餘趟數"
    ]
})

for i,m in enumerate(months,start=1):
    df_overview[m] = [
        f"{monthly_demand[i]*one_way_price:,}",
        f"{topup_list[i-1]*round_trip_price:,}",
        f"{monthly_price:,}",
        recommend_type[i-1],
        f"{round(avg_price_list[i-1]):,}",   # 四捨五入
        topup_list[i-1],
        monthly_demand[i],
        leftover_list[i-1]
    ]

styled_overview = df_overview.style.set_properties(**{'text-align':'center'})\
    .set_table_styles(common_styles)\
    .hide_index()  # <-- 完全隱藏索引
st.dataframe(styled_overview, width='stretch')

# -----------------三種票平均單價比較-----------------
st.subheader(f"{year}年度三種票平均單價比較")
df_avg = pd.DataFrame({"票種": ["單程票","回數票","月票"]})

for i,m in enumerate(months,start=1):
    df_avg[m] = [
        one_way_price if monthly_demand[i]>0 else 0,
        round(round_trip_price/multi_ticket_count) if monthly_demand[i]>0 else 0,
        round(monthly_price/monthly_demand[i]) if monthly_demand[i]>0 else 0
    ]

styled_avg = df_avg.style.format(precision=0)\
    .apply(highlight_min, axis=0)\
    .set_table_styles(common_styles)\
    .hide_index()  # <-- 完全隱藏索引
st.dataframe(styled_avg, width='stretch')

# -----------------台北/新竹上班天數表格-----------------
st.subheader(f"{year}年度台北/新竹上班天數")
df_days = pd.DataFrame({
    "項目": ["台北上班天數","新竹上班天數","總工作日"]
})
for i,m in enumerate(months,start=1):
    df_days[m] = [taipei_days_list[i-1], monthly_demand[i]//2, all_weekdays_list[i-1]]

styled_days = df_days.style.set_properties(**{'text-align':'center'})\
    .set_table_styles(common_styles)\
    .hide_index()  # <-- 完全隱藏索引
st.dataframe(styled_days, width='stretch')
