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

months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# -----------------台北上班日選擇-----------------
weekday_map = {"一":0, "二":1, "三":2, "四":3, "五":4}
taipei_workdays_str = st.multiselect("選擇台北上班日(國字)", ["一","二","三","四","五"], default=["一","二","三","四","五"])
taipei_workdays = [weekday_map[x] for x in taipei_workdays_str]

# -----------------年份選擇-----------------
year = st.number_input("選擇年度", min_value=2025, max_value=2030, value=2025)

# -----------------國定假日與補假日-----------------
holidays = [
    # 2025
    date(2025,1,1), date(2025,1,28), date(2025,1,29), date(2025,1,30), date(2025,1,31),
    date(2025,2,1), date(2025,2,2), date(2025,2,3), date(2025,2,28), date(2025,4,4),
    date(2025,4,5), date(2025,6,19), date(2025,9,28), date(2025,10,24), date(2025,10,25),
    date(2025,12,25),
    # 2026
    date(2026,1,1), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20),
    date(2026,2,21), date(2026,2,22), date(2026,2,23), date(2026,4,4), date(2026,4,5),
    date(2026,6,19), date(2026,9,28), date(2026,10,25), date(2026,10,26), date(2026,12,25)
]

def get_workdays(year, month, workdays):
    _, last_day = calendar.monthrange(year, month)
    all_days = [date(year, month, d) for d in range(1, last_day+1)]
    return [d for d in all_days if d.weekday() in workdays and d not in holidays]

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

    # 回數票成本計算，即使不推薦也要算
    topup_sets = (net_demand + multi_ticket_count -1)//multi_ticket_count if net_demand>0 else 0
    cost_m = topup_sets * round_trip_price

    # 單程票、月票成本
    cost_s = demand * one_way_price
    cost_mo = monthly_price

    # 推薦票種
    if net_demand==0:
        rec = "無需求"
        avg_price = 0
        leftover = 0
        topup = 0
    else:
        costs = {"單程票": cost_s, "回數票": cost_m, "月票": cost_mo}
        rec = min(costs, key=costs.get)
        if rec=="單程票":
            avg_price = one_way_price
            leftover = 0
            topup = 0
        elif rec=="月票":
            avg_price = round(cost_mo / net_demand)
            leftover = 0
            topup = 0
        else:  # 回數票
            avg_price = round(cost_m / net_demand)
            leftover = previous_left + topup_sets*multi_ticket_count - net_demand
            topup = topup_sets

    previous_left = leftover if rec=="回數票" else 0
    total_cost += costs[rec] if rec!="無需求" else 0

    recommend_type.append(rec)
    avg_price_list.append(avg_price)
    topup_list.append(topup)
    leftover_list.append(leftover)

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
st.dataframe(df_basic.style.set_properties(**{'width':'140px'}))

# -----------------年度票價明細-----------------
st.subheader(f"{year}年度票價明細與回數票使用情況 (當年度交通成本: {total_cost:,})")
df_overview = pd.DataFrame({
    "票種": ["單程票","回數票","月票","推薦票種","推薦票種平均單價","Top-up 次數","當月需求趟數","當月剩餘趟數"]
})
for i,m in enumerate(months,start=1):
    df_overview[m] = [
        f"{monthly_demand[i]*one_way_price:,}",
        f"{topup_list[i-1]*round_trip_price:,}",
        f"{monthly_price:,}",
        recommend_type[i-1],
        f"{avg_price_list[i-1]:,}",
        topup_list[i-1],
        monthly_demand[i],
        leftover_list[i-1]
    ]
styled_overview = df_overview.style.set_properties(**{'width':'140px','text-align':'center'})
st.dataframe(styled_overview)

# -----------------三種票平均單價比較-----------------
st.subheader(f"{year}年度三種票平均單價比較（以淨需求趟數計算）")
df_avg_price = pd.DataFrame({
    "票種":["單程票","回數票","月票"],
    **{m: [round(monthly_demand[i+1]>0 and monthly_demand[i+1]*one_way_price//monthly_demand[i+1] or 0,
               round(topup_list[i]*round_trip_price/net_demand) if net_demand>0 else 0,
               round(monthly_price/net_demand) if net_demand>0 else 0)
        for i, net_demand in enumerate([max(0, monthly_demand[j+1]- (leftover_list[j-1] if j>0 else 0)) for j in range(12)])]
       for m,i in zip(months,range(12))}
})
# 高亮最低價
def highlight_min(s):
    is_min = s.astype(float) == s.astype(float).min()
    return ['background-color: lightyellow' if v else '' for v in is_min]
styled_avg = df_avg_price.style.apply(highlight_min, axis=0).set_properties(**{'width':'140px','text-align':'center'})
st.dataframe(styled_avg)

# -----------------台北/新竹上班天數-----------------
st.subheader(f"{year}年度台北/新竹上班天數")
df_days = pd.DataFrame([taipei_days_list,[monthly_demand[i]//2 for i in range(1,13)],all_weekdays_list],
                       index=["台北上班天數","新竹上班天數","總工作日"])
df_days.columns = months
st.dataframe(df_days.style.set_properties(**{'width':'140px','text-align':'center'}))
