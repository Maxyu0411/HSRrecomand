import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import calendar

st.set_page_config(page_title="高鐵票推薦", layout="wide")
st.title("拜託讓我回台北上班QQ")
st.markdown("自行比較三種票種（單程 / 回數 / 月票）的成本與回數票使用情況")

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
    new_chu_days = len(all_weekdays) - len(taipei_days)
    monthly_demand[m] = new_chu_days*2
    taipei_days_list.append(len(taipei_days))
    all_weekdays_list.append(len(all_weekdays))

# -----------------回數票每月使用情況-----------------
df_detail = pd.DataFrame(columns=["Top-up 套數","當月需求趟數","當月剩餘次數"])
previous_left = 0
for i in range(1,13):
    demand = monthly_demand[i]
    topup = max(0, demand - previous_left)
    topup_sets = (topup + multi_ticket_count - 1)//multi_ticket_count
    left = previous_left + topup_sets*multi_ticket_count - demand
    df_detail.loc[i-1] = [topup_sets, demand, left]
    previous_left = left

# -----------------推薦票種及年度總成本-----------------
total_cost = 0
recommend_type = []
for i in range(1,13):
    demand = monthly_demand[i]
    topup_sets = df_detail.loc[i-1,"Top-up 套數"]
    cost_s = demand * one_way_price
    cost_m = topup_sets * round_trip_price
    cost_mo = monthly_price
    costs = {"單程票":cost_s,"回數票":cost_m,"月票":cost_mo}
    rec = min(costs, key=costs.get)
    recommend_type.append(rec)
    total_cost += costs[rec]

# -----------------年度票價明細表格整合回數票使用情況-----------------
df_overview = pd.DataFrame({
    "票種":["單程票","回數票","月票","推薦票種","總價","Top-up 套數","當月需求趟數","當月剩餘次數"]
})
for i, m in enumerate(months, start=1):
    df_overview[m] = [
        one_way_price*monthly_demand[i],
        df_detail.loc[i-1,"Top-up 套數"]*round_trip_price,
        monthly_price,
        recommend_type[i-1],
        (one_way_price*monthly_demand[i] if recommend_type[i-1]=="單程票" else
         df_detail.loc[i-1,"Top-up 套數"]*round_trip_price if recommend_type[i-1]=="回數票" else
         monthly_price),
        df_detail.loc[i-1,"Top-up 套數"],
        df_detail.loc[i-1,"當月需求趟數"],
        df_detail.loc[i-1,"當月剩餘次數"]
    ]

# -----------------格式化金額-----------------
def format_money(x):
    if isinstance(x, (int, float, np.integer, np.floating)):
        return f"{x:,.0f}"
    return x

# -----------------基本票價表-----------------
st.subheader("基本票價參考")
df_basic = pd.DataFrame({
    "票種":["單程票","回數票(10趟)","月票"],
    "單價":[one_way_price, round_trip_price, monthly_price]
})
st.dataframe(df_basic.style.format(format_money).hide(axis="index"), width='stretch')

# -----------------年度票價明細-----------------
st.subheader(f"{year}年度票價明細與回數票使用情況 (當年度交通成本: {total_cost:,} 元)")
st.dataframe(df_overview.style.format(format_money).hide(axis="index"), width='stretch')

# -----------------台北/新竹上班天數橫向表格-----------------
st.subheader(f"{year}年度台北/新竹上班天數")
df_days = pd.DataFrame([taipei_days_list, [monthly_demand[i]//2 for i in range(1,13)], all_weekdays_list],
                       index=["台北上班天數","新竹上班天數","總工作日加總"])
df_days.columns = months
st.dataframe(df_days, width='stretch')

