import streamlit as st
import pandas as pd
from datetime import date
import calendar
import math

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
    monthly_demand[m] = hsinchu_days * 2
    taipei_days_list.append(len(taipei_days))
    all_weekdays_list.append(len(all_weekdays))

# -----------------年度票價計算（完整邏輯）-----------------
total_cost = 0

recommend_type = []
avg_price_list = []
topup_list = []
leftover_list = []

single_costs = []
multi_costs = []
monthly_costs = []

previous_left = 0  # 上個月買回數票後剩下的趟數（internal state）

for i in range(1, 13):
    demand = monthly_demand[i]
    prev_left_old = previous_left  # 本月一開始的剩餘趟數（來自上個月購買回數票）
    
    # 先用掉上月剩餘（如果有）
    used_from_previous = min(prev_left_old, demand)
    remaining_need = demand - used_from_previous  # 這才是要靠本月新購票（或單程/月票）解決的趟數

    # 若 remaining_need > 0，計算如果買回數票需要 top-up 幾套與成本（這是「假設買回數票」的成本）
    if remaining_need > 0:
        topup_sets_if_multi = (remaining_need + multi_ticket_count - 1) // multi_ticket_count
    else:
        topup_sets_if_multi = 0
    multi_cost_if_buy = topup_sets_if_multi * round_trip_price

    # 三種票的「本月會產生的成本（若選該票種）」：
    single_cost = demand * one_way_price
    monthly_cost = monthly_price
    multi_cost = multi_cost_if_buy  # 表示若選回數票，本月需要花的 top-up 成本（若 remaining_need==0，則 multi_cost==0）

    # 存下三種「本月成本（理論）」以便在表格中顯示
    single_costs.append(single_cost)
    multi_costs.append(multi_cost)
    monthly_costs.append(monthly_cost)

    # 若 remaining_need == 0，代表不需要在本月購買任何新回數票（上月剩餘就足夠）
    if remaining_need == 0:
        rec = "無需求"
        avg_price = 0
        topup = 0
        # 更新 internal previous_left（被消耗後還剩多少）
        previous_left = prev_left_old - used_from_previous
        leftover_display = 0  # 顯示上表時，不顯示剩餘（使用者要求：只在推薦回數票時顯示剩餘）
    else:
        # 比較三種票的成本（用上述的 single_cost, multi_cost, monthly_cost）
        costs = {"單程票": single_cost, "回數票": multi_cost, "月票": monthly_cost}
        rec = min(costs, key=costs.get)

        if rec == "單程票":
            avg_price = one_way_price if demand > 0 else 0
            topup = 0
            # 使用了上月剩餘（已在 remaining_need = demand - used_from_previous 計算），但沒有買新的套票
            previous_left = prev_left_old - used_from_previous
            leftover_display = 0
        elif rec == "月票":
            avg_price = monthly_cost // demand if demand > 0 else 0
            topup = 0
            previous_left = prev_left_old - used_from_previous
            leftover_display = 0
        else:  # rec == "回數票"
            # 若選回數票，實際會買 topup_sets_if_multi 套，且剩餘變成：
            topup = topup_sets_if_multi
            # new leftover = (prev_left_old - used_from_previous) + bought_trips - used_in_remaining
            bought_trips = topup * multi_ticket_count
            # 用掉 used_from_previous（已扣），再用 remaining_need（也已扣），買入的 trips 被用掉 remaining_need
            previous_left = (prev_left_old - used_from_previous) + bought_trips - remaining_need
            # 本月回數票實際花費 = multi_cost（已算）
            avg_price = int(round(multi_cost / remaining_need)) if remaining_need > 0 else 0
            leftover_display = previous_left  # 顯示剩餘趟數（只有回數票時顯示）

    # 累計總成本：只有實際被推薦（選擇）的票種其成本才會加到 total_cost
    if rec == "單程票":
        total_cost += single_cost
    elif rec == "月票":
        total_cost += monthly_cost
    elif rec == "回數票":
        total_cost += multi_cost
    else:  # 無需求 -> no cost
        pass

    recommend_type.append(rec)
    avg_price_list.append(int(avg_price))
    topup_list.append(int(topup))
    leftover_list.append(int(leftover_display))

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
st.dataframe(df_basic.style.hide(axis="index"), width='stretch')

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

for i, m in enumerate(months, start=1):
    df_overview[m] = [
        f"{single_costs[i-1]:,}",
        f"{multi_costs[i-1]:,}",
        f"{monthly_costs[i-1]:,}",
        recommend_type[i-1],
        f"{avg_price_list[i-1]:,}",
        topup_list[i-1],
        monthly_demand[i],
        leftover_list[i-1]
    ]

styled_overview = df_overview.style.set_properties(**{'text-align':'center'}).hide(axis="index")
st.dataframe(styled_overview, width='stretch')

# -----------------台北/新竹上班天數表格-----------------
st.subheader(f"{year}年度台北/新竹上班天數")
df_days = pd.DataFrame([taipei_days_list, [monthly_demand[i]//2 for i in range(1,13)], all_weekdays_list],
                       index=["台北上班天數","新竹上班天數","總工作日"])
df_days.columns = months
st.dataframe(df_days.style.set_properties(**{'text-align':'center'}), width='stretch')

