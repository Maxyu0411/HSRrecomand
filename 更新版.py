import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
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

year = st.number_input("選擇年度", min_value=2025, max_value=2030, value=2025)

# -----------------國定假日(含補班)-----------------
holidays = {
    holidays_dict = {
    2025: [
        "2025-01-01",  # 元旦
        "2025-01-25","2025-01-26","2025-01-27","2025-01-28","2025-01-29","2025-01-30","2025-01-31","2025-02-01","2025-02-02",  # 春節
        "2025-02-28","2025-03-01","2025-03-02",  # 和平紀念日
        "2025-04-03","2025-04-04","2025-04-05","2025-04-06",  # 兒童節、清明節
        "2025-05-01",  # 勞動節
        "2025-05-30","2025-05-31","2025-06-01",  # 端午節
        "2025-09-27","2025-09-28","2025-09-29",  # 教師節
        "2025-10-04","2025-10-05","2025-10-06",  # 中秋節
        "2025-10-10","2025-10-11","2025-10-12",  # 國慶日
        "2025-10-24","2025-10-25","2025-10-26",  # 光復節
        "2025-12-25"  # 行憲紀念日
    ],
    2026: [
        "2026-01-01",  # 元旦
        "2026-02-14","2026-02-15","2026-02-16","2026-02-17","2026-02-18","2026-02-19","2026-02-20","2026-02-21","2026-02-22",  # 春節
        "2026-02-27","2026-02-28","2026-03-01",  # 和平紀念日
        "2026-04-03","2026-04-04","2026-04-05","2026-04-06",  # 兒童節、清明節
        "2026-05-01",  # 勞動節
        "2026-06-19","2026-06-20","2026-06-21",  # 端午節
        "2026-09-25","2026-09-26","2026-09-27","2026-09-28",  # 中秋節、教師節
        "2026-10-09","2026-10-10","2026-10-11","2026-10-12",  # 國慶日
        "2026-10-24","2026-10-25"  # 光復節
    ]
}
holidays = [pd.to_datetime(d) for d in holidays.get(year, [])]

# -----------------取得當月工作日-----------------
def get_workdays(year, month, workdays):
    _, last_day = calendar.monthrange(year, month)
    all_days = [date(year, month, d) for d in range(1, last_day+1)]
    workdays_list = [d for d in all_days if d.weekday() in workdays and pd.to_datetime(d) not in holidays]
    return workdays_list

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
previous_left = 0
recommend_type = []
avg_price_list = []
topup_list = []
leftover_list = []
cost_s_list = []
cost_m_list = []
cost_mo_list = []
avg_price_detail = []

for i in range(1, 13):
    demand = monthly_demand[i]
    net_demand = max(0, demand - previous_left)

    # 計算成本
    topup_sets = (net_demand + multi_ticket_count - 1) // multi_ticket_count if net_demand > 0 else 0
    cost_m = topup_sets * round_trip_price
    cost_s = net_demand * one_way_price
    cost_mo = monthly_price

    avg_s = one_way_price if net_demand>0 else 0
    avg_m = round(cost_m / net_demand) if net_demand>0 else 0
    avg_mo = round(cost_mo / demand) if demand>0 else 0
    avg_dict = {"單程票": avg_s, "回數票": avg_m, "月票": avg_mo}

    # 推薦票種
    if net_demand == 0:
        rec = "無需求"
        avg_price = 0
        topup = 0
        leftover = 0
        previous_left = 0
    elif net_demand <= multi_ticket_count and cost_m > cost_s:
        rec = "單程票"
        avg_price = avg_s
        topup = 0
        leftover = 0
        previous_left = 0
    else:
        rec = min(avg_dict, key=avg_dict.get)
        avg_price = avg_dict[rec]
        if rec == "回數票":
            leftover = topup_sets * multi_ticket_count - net_demand
            previous_left = leftover
            topup = topup_sets
        else:
            leftover = 0
            previous_left = 0
            topup = 0

    total_cost += {"單程票": cost_s, "回數票": cost_m, "月票": cost_mo, "無需求":0}[rec]

    recommend_type.append(rec)
    avg_price_list.append(avg_price)
    topup_list.append(topup)
    leftover_list.append(leftover)
    cost_s_list.append(cost_s)
    cost_m_list.append(cost_m)
    cost_mo_list.append(cost_mo)
    avg_price_detail.append({"單程票": avg_s, "回數票": avg_m, "月票": avg_mo})

net_demand_list = [max(0, monthly_demand[i] - (leftover_list[i-2] if i>1 else 0)) for i in range(1,13)]

# -----------------固定第一欄寬度-----------------
first_col_style = [{
    'selector': 'th:nth-child(1), td:nth-child(1)',
    'props': [('min-width', '140px'), ('max-width', '140px'), ('text-align', 'center')]
}]

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
st.dataframe(df_basic.style.set_table_styles(first_col_style), width='stretch')

# -----------------年度票價明細-----------------
st.subheader(f"{year}年度票價明細與回數票使用情況 (當年度交通成本: {total_cost:,})")
df_overview = pd.DataFrame({
    "項目": [
        "單程票成本","回數票成本","月票成本","推薦票種","推薦票種平均單價",
        "Top-up 次數","淨需求趟數","當月需求趟數","當月剩餘趟數"
    ]
})
for i,m in enumerate(months,start=1):
    df_overview[m] = [
        f"{cost_s_list[i-1]:,}",
        f"{cost_m_list[i-1]:,}",
        f"{cost_mo_list[i-1]:,}",
        recommend_type[i-1],
        f"{avg_price_list[i-1]:,}",
        topup_list[i-1],
        net_demand_list[i-1],
        monthly_demand[i],
        leftover_list[i-1]
    ]
st.dataframe(df_overview.style.set_table_styles(first_col_style), width='stretch')

# -----------------三種票平均單價比較-----------------
st.subheader(f"{year}年度三種票平均單價比較 (最低單價高亮)")
df_avg = pd.DataFrame({"票種": ["單程票","回數票","月票"]})
for i,m in enumerate(months,start=1):
    df_avg[m] = [
        avg_price_detail[i-1]["單程票"],
        avg_price_detail[i-1]["回數票"],
        avg_price_detail[i-1]["月票"]
    ]

def highlight_min_per_month(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    for month in df.columns[1:]:
        min_val = df[month].min()
        styles.loc[df[month] == min_val, month] = 'color: black; background-color: #ffff99'
    return styles

styled_avg = df_avg.style.set_table_styles(first_col_style).apply(highlight_min_per_month, axis=None)
st.dataframe(styled_avg, width='stretch')

# -----------------台北/新竹上班天數表格-----------------
st.subheader(f"{year}年度台北/新竹上班天數")
df_days = pd.DataFrame({"項目": ["台北上班天數","新竹上班天數","總工作日"]})
for i,m in enumerate(months,start=1):
    df_days[m] = [taipei_days_list[i-1], monthly_demand[i]//2, all_weekdays_list[i-1]]
st.dataframe(df_days.style.set_table_styles(first_col_style), width='stretch')
