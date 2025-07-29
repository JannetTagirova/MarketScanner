import streamlit as st
import pandas as pd
import requests

# -------------- API и функция запроса цены с кэшированием --------------
API_KEYS = [
    'HAMSCSQ3556Y6DNIPCBB4AYZEN2QXVXDMI',
    'MQGFCGHDWJ2XR18I2MBYRSZ86F9GXND3XN',
    'WSAFV4QJFRGF1HUQWTIEVF9YKT5DHESDH5'
]

@st.cache_data(ttl=3600)
def get_cryptorank_market_data(coin_id):
    API_KEY = "324ef173179638466f55906382cf58bc21df8bc05f37e292d165f5ff958e"
    url = f"https://api.cryptorank.io/v2/currencies/{coin_id}"
    try:
        response = requests.get(url, headers={"X-Api-Key": API_KEY}, timeout=10)
        if response.ok:
            data = response.json().get("data", {})
            market_cap = data.get("marketCap")
            volume_24h = data.get("volume24h")
            return market_cap, volume_24h
    except Exception:
        pass
    return None, None


@st.cache_data(ttl=60*60*4)
def get_token_price_cached(contract_address, api_key):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": 1,
        "module": "token",
        "action": "tokeninfo",
        "contractaddress": contract_address,
        "apikey": api_key
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get('status') == '1' and 'result' in data:
            token_info = data['result'][0]
            price_str = token_info.get('tokenPriceUSD')
            if price_str and float(price_str) > 0:
                return float(price_str)
            else:
                # Цена либо отсутствует, либо равна нулю
                return None
        return None
    except Exception:
        return None

def show_top_changes(df, value_col, change_col):
    if df.empty: return None, None
    max_row = df.loc[df[change_col].idxmax()]
    min_row = df.loc[df[change_col].idxmin()]
    return max_row, min_row

def format_numbers(val):
    try:
        if isinstance(val, (int, float)):
            return f"{int(val):,}".replace(",", " ")
        # если проценты в виде строки типа "2.25%"
        if isinstance(val, str) and val.replace('.', '', 1).replace(' ', '').isdigit():
            return f"{val:,}".replace(",", " ")
    except Exception:
        return val
    return val

def align_style(s):
    # выравнивание: адреса и названия - влево, числа и проценты - по центру
    if s.name in ["Exchange Name", "Exchange's Wallet Address"]:
        return ['text-align: left'] * len(s)
    else:
        return ['text-align: center'] * len(s)

def header_style(s):
    return [
        'font-weight: bold; text-align: center; vertical-align: middle; background: #fafbfc;'
        for _ in s
    ]

def color_change(val):
    try:
        if isinstance(val, str):
            val = val.replace('%', '')
        val = float(val)
        if val > 0:
            color = 'green'
        elif val < 0:
            color = 'red'
        else:
            color = 'black'
    except Exception:
        color = 'black'
    return f'color: {color}'

def bold_exchange(val):
    return 'font-weight: bold;' if val else ''

def styled_df_ex(df):
    styled = (
        df.style
          .format({"Token's Count": format_numbers})
          .applymap(color_change, subset=["24h Change"])
          .apply(align_style)
          .applymap(bold_exchange, subset=["Exchange Name"])
          .set_table_styles([
              {'selector': 'th', 'props': 'font-weight: bold; text-align: center; background-color: #fafbfc;'}
          ])
          .set_properties(**{'border': '1px solid #F0F0F0', 'font-size': '16px'})
    )
    # Скрытие индекса для разных версий pandas:
    try:  # новые версии pandas
        html = styled.hide(axis="index").to_html()
    except AttributeError:  # старые версии pandas
        html = styled.to_html(index=False)
    return html


def styled_df(df):
    styled = (
        df.style
         .format({"Token's Count": format_numbers})
         .applymap(color_change, subset=["24h Change"])
         .apply(align_style)
         .set_table_styles([
             {'selector': 'th', 'props': 'font-weight: bold; text-align: center; background-color: #fafbfc;'}
         ])
         .set_properties(**{'border': '1px solid #F0F0F0', 'font-size': '16px'})
    )
    # Скрытие индекса для разных версий pandas:
    try:  # новые версии pandas
        html = styled.hide(axis="index").to_html()
    except AttributeError:  # старые версии pandas
        html = styled.to_html(index=False)
    return html


def format_money(val):
    try:
        return "$" + "{:,.0f}".format(float(val)).replace(",", " ")
    except:
        return "--"
# ------------------ Загрузка таблиц ------------------
df = pd.read_excel('input_eth.xlsx')
exchange_balances_df = pd.read_excel('exchanges_balances.xlsx')
holders_balances_df = pd.read_excel('holders_balances.xlsx')

st.set_page_config(page_title="Crypto Explorer", layout="wide")
page = st.sidebar.radio("Go to:", ["Main", "О программе"])

if page == "Main":
    st.title("Tokens list")
    coin_names = df["long"].tolist()
    selected_coin = st.selectbox("Tokens:", coin_names)
    st.markdown("---")
    coin = df[df["long"] == selected_coin].iloc[0]

    # --- Страницы под названием монеты ---
    tab_titles = ["Token's data", "Exchanges", "Holders"]
    tabs = st.tabs(tab_titles)
    
    # --- Управление состояниями ---
    if "prev_coin" not in st.session_state:
        st.session_state["prev_coin"] = None
    if "show_token_data" not in st.session_state:
        st.session_state["show_token_data"] = False
    if "show_all_exchanges" not in st.session_state:
        st.session_state["show_all_exchanges"] = False
    if "show_all_holders" not in st.session_state:
        st.session_state["show_all_holders"] = False

    # Сброс состояний при выборе другой монеты
    if st.session_state["prev_coin"] != coin["long"]:
        st.session_state["show_token_data"] = False
        st.session_state["show_all_exchanges"] = False
        st.session_state["show_all_holders"] = False
        st.session_state["prev_coin"] = coin["long"]

    # Кнопка для показа данных токена
    with tabs[0]:

        
    # --- Блок: иконка и название ---
        
        icon_url = coin.get("icon")
        name = coin['short']
        
        if pd.notnull(icon_url):
            st.markdown(
                f"""
                <span style='display: flex; align-items: center; font-size:2.0em; font-weight:700;'>
                    <img src="{icon_url}" style="width:40px; vertical-align:middle; margin-right: 0.5em;">
                    &nbsp;&nbsp;{name}
                </span>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<span style='font-size:2.0em; font-weight:700;'>{name}</span>",
                unsafe_allow_html=True
            )
        
            
        
        # --- Крупная цена монеты, по левому краю ---
        contract_address = coin.get('address')
        price = None
        if pd.notnull(contract_address):
            key_i = coin.name % len(API_KEYS)
            price = get_token_price_cached(contract_address, api_key=API_KEYS[key_i])
            if price is not None:
                st.markdown(
                    f"<div style='font-size:1.8em; font-weight: 700; margin:12px 0 18px 0; text-align:left'>"
                    f" ${price:,.6f}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div style='font-size:1.8em; font-weight: 700; margin:12px 0 18px 0; text-align:left'>"
                    "💸 -- (не удалось получить с API)"
                    "</div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                "<div style='font-size:1.8em; font-weight: 700; margin:12px 0 18px 0; text-align:left'>"
                "💸 -- (нет адреса контракта)"
                "</div>",
                unsafe_allow_html=True
            )
    
        # --- Подготовка данных для таблицы ---
        
        circ_value = coin.get('circ')
        circulating = "{:,.0f}".format(float(circ_value)).replace(",", " ") if pd.notnull(circ_value) else "--"
        full_name = coin.get('long', '--')
        blockchain = coin.get('Сеть (блокчейн)', '--')
        
        coin_id = coin.get("id")
        cap, vol = None, None
        if pd.notnull(coin_id):
            cap, vol = get_cryptorank_market_data(coin_id)
            cap = format_money(cap) if cap is not None and str(cap).replace('.', '', 1).isdigit() else "--"
            vol = format_money(vol) if vol is not None and str(vol).replace('.', '', 1).isdigit() else "--"
        else:
            cap, vol = "--", "--"

    
        # --- Информация о токене в виде таблицы, выравнивание влево ---
        
        info_table = f"""
        <table style="margin-top:10px; text-align:left;">
            <tr><th align='left'>Market Cap</th><td>{cap}</td></tr>
            <tr><th align='left'>24h Volume</th><td>{vol}</td></tr>
            <tr><th align='left'>Circulating Supply</th><td>{circulating}</td></tr>
            <tr><th align='left'>Token Full Name</th><td>{full_name}</td></tr>
            <tr><th align='left'>Blockchain</th><td>{blockchain}</td></tr>
        </table>
        """
        st.markdown(info_table, unsafe_allow_html=True)


        
        # --- Блок бирж ---
        
        st.markdown("*--* 🏦 Актуальная биржевая информация (наибольшие положительный и отрицательный приросты)")

        coin_exchanges = exchange_balances_df[exchange_balances_df['long_name'] == coin['long']].copy()
        
        if not coin_exchanges.empty:
            exchanges_show = coin_exchanges[['Name', 'holder_adress', 'coins_count', 'change']].copy()
            exchanges_show['coins_count'] = exchanges_show['coins_count'].astype(int)
            exchanges_show['change'] = exchanges_show['change'].astype(str).str.replace('%', '', regex=False).str.replace(' ', '', regex=False).astype(float)
        
            if pd.notnull(circ_value) and circ_value > 0:
                exchanges_show["percent"] = exchanges_show["coins_count"] / circ_value * 100
            else:
                exchanges_show["percent"] = 0.0
        
            # Находим с максимальным и минимальным приростом
            
            max_inc = exchanges_show.loc[exchanges_show['change'].idxmax()]
            max_dec = exchanges_show.loc[exchanges_show['change'].idxmin()]
        
            # Если это одна и та же биржа -- показываем только одну запись
            
            if max_inc['Name'] == max_dec['Name']:
                filtered_ex = pd.DataFrame([max_inc])
            else:
                filtered_ex = pd.DataFrame([max_inc, max_dec])
        
            # Сортировка по percent
            
            filtered_ex = filtered_ex.sort_values("percent", ascending=False)
            filtered_ex['percent'] = filtered_ex['percent'].map(lambda x: f"{x:.2f}%")
            filtered_ex['change'] = filtered_ex['change'].map(lambda x: f"{x:.2f}%")
        
            # Переименуем столбцы
            filtered_ex = filtered_ex.rename(columns={
                "Name": "Exchange Name",
                "holder_adress": "Exchange's Wallet Address",
                "coins_count": "Token's Count",
                "change": "24h Change",
                "percent": "Percent of Emission"
            })
        
            # Укажи нужный порядок столбцов
            ex_show_columns = [
                "Exchange Name",
                "Token's Count",
                "24h Change",
                "Percent of Emission"
            ]
        
            # Применяем стилизацию
            styled = (
                filtered_ex[ex_show_columns]
                .style
                .format({"Token's Count": format_numbers})
                .applymap(color_change, subset=["24h Change"])
                .apply(align_style)
                .set_table_styles([
                    {'selector': 'th', 'props': 'font-weight: bold; text-align: center; background-color: #fafbfc;'}
                ])
            )

            # filtered — ваш DataFrame!
            styled_html = styled_df_ex(filtered_ex[ex_show_columns])
            
            st.markdown(styled_html, unsafe_allow_html=True)
        
        else:
            st.info("ℹ️ Нет данных о биржах для этой монеты.")




        
        # --- Блок держателей ---

        st.markdown("*--* 👤 Актуальная информация по держателям (наибольшие положительный и отрицательный приросты)")

        coin_holders = holders_balances_df[holders_balances_df['long_name'] == coin['long']].copy()
        
        if not coin_holders.empty:
            holders_show = coin_holders[['holder_adress', 'coins_count', 'change']].copy()
            holders_show['coins_count'] = holders_show['coins_count'].astype(int)
            holders_show['change'] = holders_show['change'].astype(str).str.replace('%', '', regex=False).str.replace(' ', '', regex=False).astype(float).astype(float)
        
            if pd.notnull(circ_value) and circ_value > 0:
                holders_show["percent"] = (holders_show["coins_count"] / circ_value * 100)
            else:
                holders_show["percent"] = 0.0
        
            # Находим с максимальным и минимальным приростом
            
            max_inc = holders_show.loc[holders_show['change'].idxmax()]
            max_dec = holders_show.loc[holders_show['change'].idxmin()]
        
            # Если это одна и та же биржа — показываем только одну запись
            
            if max_inc['holder_adress'] == max_dec['holder_adress']:
                filtered = pd.DataFrame([max_inc])
            else:
                filtered = pd.DataFrame([max_inc, max_dec])
            
            # Сортировка по percent
            
            filtered = filtered.sort_values("percent", ascending=False)
            filtered['percent'] = filtered['percent'].map(lambda x: f"{x:.2f}%")
            filtered['change'] = filtered['change'].map(lambda x: f"{x:.2f}%")
        
            filtered = filtered.rename(columns={
                "holder_adress": "Holder's Wallet Address",
                "coins_count": "Token's Count",
                "change": "24h Change",
                "percent": "Percent of Emission"
            })
        
            # Укажи нужный порядок столбцов
            show_columns = [
                "Holder's Wallet Address",
                "Token's Count",
                "24h Change",
                "Percent of Emission"
            ]
        
            # Применяем стилизацию
            styled = (
                filtered[show_columns]
                .style
                .format({"Token's Count": format_numbers})
                .applymap(color_change, subset=["24h Change"])
                .apply(align_style)
                .set_table_styles([
                    {'selector': 'th', 'props': 'font-weight: bold; text-align: center; background-color: #fafbfc;'}
                ])
            )

            # filtered — ваш DataFrame!
            styled_html = styled_df(filtered[show_columns])
            
            st.markdown(styled_html, unsafe_allow_html=True)
        
        else:
            st.info("ℹ️ Нет данных о держателях для этой монеты.")
        








# --- Страница бирж, где есть токен ---

    with tabs[1]:
        
        # --- Блок бирж, где есть токен ---
        
        st.markdown("*--* 🏦 Биржи, на которых доступна монета")
        
        coin_exchanges = exchange_balances_df[exchange_balances_df['long_name'] == coin['long']].copy()
        
        if not coin_exchanges.empty:
            # Формируем таблицу для отображения
            exchanges_show = coin_exchanges[['Name', 'holder_adress', 'coins_count', 'change']].copy()
            exchanges_show['coins_count'] = exchanges_show['coins_count'].astype(int)
            exchanges_show = exchanges_show.sort_values('coins_count', ascending=False).reset_index(drop=True)
        
            # Добавляем столбец процентов
            if pd.notnull(circ_value) and circ_value > 0:
                exchanges_show["percent"] = (exchanges_show["coins_count"] / circ_value * 100).map(lambda x: f"{x:.2f}%")
            else:
                exchanges_show["percent"] = "--"
        
            top5_ex = exchanges_show.head(5)
            rest_ex = exchanges_show.iloc[5:]

            exchanges_show = exchanges_show.rename(columns={
                "Name": "Exchange Name",
                "holder_adress": "Exchange's Wallet Address",
                "coins_count": "Token's Count",
                "change": "24h Change",
                "percent": "Percent of Emission"
            })
            
            # Укажи нужный порядок столбцов
            ex_show_columns_full = [
                "Exchange Name",
                "Token's Count",
                "24h Change",
                "Percent of Emission"
            ]
        
            # Применяем стилизацию
            styled = (
                exchanges_show[ex_show_columns_full]
                .style
                .format({"Token's Count": format_numbers})
                .applymap(color_change, subset=["24h Change"])
                .apply(align_style)
                .set_table_styles([
                    {'selector': 'th', 'props': 'font-weight: bold; text-align: center; background-color: #fafbfc;'}
                ])
            )

            # filtered — ваш DataFrame!
            styled_html = styled_df_ex(exchanges_show[ex_show_columns_full])
            
            st.markdown(styled_html, unsafe_allow_html=True)
            
        else:
            st.info("ℹ️ Нет данных о биржах для этой монеты.")
    
    
    
    
    
    
    
    
    
    # --- Страница держателей токена ---
    
    with tabs[2]:
    
        st.markdown("*--* 👤 Держатели монеты")
        
        coin_holders = holders_balances_df[holders_balances_df['long_name'] == coin['long']].copy()
        
        if not coin_holders.empty:
            # Формируем таблицу для отображения
            holders_show = coin_holders[['Name', 'holder_adress', 'coins_count', 'change']].copy()
            holders_show['coins_count'] = holders_show['coins_count'].astype(int)
            holders_show = holders_show.sort_values('coins_count', ascending=False).reset_index(drop=True)
        
            # Добавляем столбец процентов
            if pd.notnull(circ_value) and circ_value > 0:
                holders_show["percent"] = (holders_show["coins_count"] / circ_value * 100).map(lambda x: f"{x:.2f}%")
            else:
                holders_show["percent"] = "--"
        
            top5 = holders_show.head(5)
            rest = holders_show.iloc[5:]
            
            holders_show = holders_show.rename(columns={
                "holder_adress": "Holder's Wallet Address",
                "coins_count": "Token's Count",
                "change": "24h Change",
                "percent": "Percent of Emission"
            })
            
            # Укажи нужный порядок столбцов
            show_columns_full = [
                "Holder's Wallet Address",
                "Token's Count",
                "24h Change",
                "Percent of Emission"
            ]
        
            # Применяем стилизацию
            styled = (
                holders_show[show_columns_full]
                .style
                .format({"Token's Count": format_numbers})
                .applymap(color_change, subset=["24h Change"])
                .apply(align_style)
                .set_table_styles([
                    {'selector': 'th', 'props': 'font-weight: bold; text-align: center; background-color: #fafbfc;'}
                ])
            )

            # filtered — ваш DataFrame!
            styled_html = styled_df(holders_show[show_columns_full])
            
            st.markdown(styled_html, unsafe_allow_html=True)
            
        else:
            st.info("ℹ️ Нет данных о держателях для этой монеты.")
    
    
    




elif page == "О программе":
    st.markdown("""
    *--* Crypto Explorer

    Лёгкое приложение для просмотра данных о монетах из Excel-таблицы.
    """)