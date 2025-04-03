import streamlit as st
import pandas as pd
from vnstock import Vnstock
from datetime import datetime, timedelta

st.set_page_config(page_title="Hữu Quang Chứng Khoán", layout="wide")

st.title("Hữu Quang Chứng Khoán")
st.subheader("Ứng dụng Tra cứu Tin tức, Sự kiện và giao dịch nội bộ")

# Hàm lấy tin tức của cổ phiếu (nguồn VCI)
def get_stock_news(symbol):
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        news_df = stock.company.news()
        # Đảm bảo cột ngày là cột đầu tiên nếu có
        if 'published_date' in news_df.columns:
            cols = ['published_date'] + [col for col in news_df.columns if col != 'published_date']
            news_df = news_df[cols]
        return news_df
    except Exception as e:
        st.error(f"Lỗi khi lấy tin tức: {e}")
        return pd.DataFrame()

# Hàm lấy sự kiện của cổ phiếu (nguồn VCI)
def get_stock_events(symbol):
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        events_df = stock.company.events()
        # Đảm bảo cột ngày là cột đầu tiên nếu có
        if 'event_date' in events_df.columns:
            cols = ['event_date'] + [col for col in events_df.columns if col != 'event_date']
            events_df = events_df[cols]
        return events_df
    except Exception as e:
        st.error(f"Lỗi khi lấy sự kiện: {e}")
        return pd.DataFrame()

# Hàm lấy giao dịch nội bộ của cổ phiếu (nguồn TCBS)
def get_insider_deals(symbol):
    try:
        stock = Vnstock().stock(symbol=symbol, source='TCBS')
        insider_deals_df = stock.company.insider_deals()
        # Đảm bảo cột ngày là cột đầu tiên nếu có
        if 'dealAnnounceDate' in insider_deals_df.columns:
            cols = ['dealAnnounceDate'] + [col for col in insider_deals_df.columns if col != 'dealAnnounceDate']
            insider_deals_df = insider_deals_df[cols]
        return insider_deals_df
    except Exception as e:
        st.error(f"Lỗi khi lấy giao dịch nội bộ: {e}")
        return pd.DataFrame()

# Hàm lấy lịch sử giá của cổ phiếu (nguồn VCI)
def get_price_history(symbol, start_date, end_date):
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        history_df = stock.quote.history(start=start_date.strftime('%Y-%m-%d'),
                                         end=end_date.strftime('%Y-%m-%d'),
                                         interval='1D')
        # Đảm bảo cột ngày nằm ở vị trí đầu tiên nếu có
        if 'time' in history_df.columns:
            cols = ['time'] + [col for col in history_df.columns if col != 'time']
            history_df = history_df[cols]
        return history_df
    except Exception as e:
        st.error(f"Lỗi khi lấy lịch sử giá: {e}")
        return pd.DataFrame()

# Sidebar: cài đặt và tùy chọn người dùng
st.sidebar.header("Tùy chọn")

# Nhập mã cổ phiếu (mặc định là "ACV")
ticker_input = st.sidebar.text_input("Nhập mã cổ phiếu:", "ACV")

# Chọn khoảng thời gian (cho tin tức, sự kiện và lịch sử giá)
st.sidebar.subheader("Khoảng thời gian")
end_date = datetime.now()
start_date = end_date - timedelta(days=365)  # Mặc định 1 năm trước
start_date_input = st.sidebar.date_input("Từ ngày:", start_date)
end_date_input = st.sidebar.date_input("Đến ngày:", end_date)

# Tùy chọn cho giao dịch nội bộ (biến page_size có thể dùng sau nếu cần)
st.sidebar.subheader("Giao dịch nội bộ")
page_size = st.sidebar.slider("Số lượng bản ghi:", min_value=10, max_value=100, value=50, step=10)

# Tạo giao diện gồm 4 tab: Sự kiện, Tin tức, Giao dịch nội bộ, Lịch sử giá
tab1, tab2, tab3, tab4 = st.tabs(["Sự kiện", "Tin tức", "Giao dịch nội bộ", "Lịch sử giá"])

# Tab Sự kiện
with tab1:
    st.header(f"Sự kiện của cổ phiếu {ticker_input}")
    if st.button("Tải dữ liệu sự kiện"):
        with st.spinner("Đang tải dữ liệu..."):
            events_df = get_stock_events(ticker_input)
            if not events_df.empty:
                if "event_date" in events_df.columns:
                    events_df["event_date"] = pd.to_datetime(events_df["event_date"])
                    mask = (events_df["event_date"] >= pd.to_datetime(start_date_input)) & (events_df["event_date"] <= pd.to_datetime(end_date_input))
                    filtered_events = events_df.loc[mask]
                else:
                    filtered_events = events_df
                st.dataframe(filtered_events)
                csv = filtered_events.to_csv(index=False).encode("utf-8-sig")
                st.download_button(label="Tải xuống dữ liệu sự kiện (CSV)",
                                   data=csv,
                                   file_name=f"{ticker_input}_events_{start_date_input}_{end_date_input}.csv",
                                   mime="text/csv")
            else:
                st.info(f"Không có dữ liệu sự kiện cho {ticker_input}")

# Tab Tin tức
with tab2:
    st.header(f"Tin tức của cổ phiếu {ticker_input}")
    if st.button("Tải dữ liệu tin tức"):
        with st.spinner("Đang tải dữ liệu..."):
            news_df = get_stock_news(ticker_input)
            if not news_df.empty:
                if "published_date" in news_df.columns:
                    news_df["published_date"] = pd.to_datetime(news_df["published_date"])
                    mask = (news_df["published_date"] >= pd.to_datetime(start_date_input)) & (news_df["published_date"] <= pd.to_datetime(end_date_input))
                    filtered_news = news_df.loc[mask]
                else:
                    filtered_news = news_df
                st.dataframe(filtered_news)
                csv = filtered_news.to_csv(index=False).encode("utf-8-sig")
                st.download_button(label="Tải xuống dữ liệu tin tức (CSV)",
                                   data=csv,
                                   file_name=f"{ticker_input}_news_{start_date_input}_{end_date_input}.csv",
                                   mime="text/csv")
            else:
                st.info(f"Không có dữ liệu tin tức cho {ticker_input}")

# Tab Giao dịch nội bộ
with tab3:
    st.header(f"Giao dịch nội bộ của cổ phiếu {ticker_input}")
    if st.button("Tải dữ liệu giao dịch nội bộ"):
        with st.spinner("Đang tải dữ liệu..."):
            insider_deals_df = get_insider_deals(ticker_input)
            if not insider_deals_df.empty:
                if "dealAnnounceDate" in insider_deals_df.columns:
                    insider_deals_df["dealAnnounceDate"] = pd.to_datetime(insider_deals_df["dealAnnounceDate"])
                    mask = (insider_deals_df["dealAnnounceDate"] >= pd.to_datetime(start_date_input)) & (insider_deals_df["dealAnnounceDate"] <= pd.to_datetime(end_date_input))
                    filtered_deals = insider_deals_df.loc[mask]
                else:
                    filtered_deals = insider_deals_df
                st.dataframe(filtered_deals)
                csv = filtered_deals.to_csv(index=False).encode("utf-8-sig")
                st.download_button(label="Tải xuống dữ liệu giao dịch nội bộ (CSV)",
                                   data=csv,
                                   file_name=f"{ticker_input}_insider_deals_{start_date_input}_{end_date_input}.csv",
                                   mime="text/csv")
            else:
                st.info(f"Không có dữ liệu giao dịch nội bộ cho {ticker_input}")

# Tab Lịch sử giá
with tab4:
    st.header(f"Lịch sử giá cổ phiếu {ticker_input}")
    col1, col2 = st.columns(2)
    # Nút tải dữ liệu lịch sử giá theo khoảng thời gian đã chọn
    with col1:
        if st.button("Tải lịch sử giá theo thời gian", key="load_selected_history"):
            with st.spinner("Đang tải dữ liệu..."):
                price_history_df = get_price_history(ticker_input, start_date_input, end_date_input)
                if not price_history_df.empty:
                    st.dataframe(price_history_df)
                    csv = price_history_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(label="Tải xuống lịch sử giá đã chọn (CSV)",
                                       data=csv,
                                       file_name=f"{ticker_input}_price_history_{start_date_input}_{end_date_input}.csv",
                                       mime="text/csv",
                                       key="download_selected_history")
                else:
                    st.info(f"Không có dữ liệu lịch sử giá cho {ticker_input}")
    # Nút tải toàn bộ lịch sử giá (không giới hạn thời gian)
    with col2:
        if st.button("Tải toàn bộ lịch sử giá", key="load_full_history"):
            with st.spinner("Đang tải toàn bộ lịch sử giá..."):
                far_past_date = datetime.now() - timedelta(days=365*20)  # Lấy dữ liệu từ 20 năm trước
                full_price_history_df = get_price_history(ticker_input, far_past_date, datetime.now())
                if not full_price_history_df.empty:
                    st.dataframe(full_price_history_df)
                    csv = full_price_history_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(label="Tải xuống toàn bộ lịch sử giá (CSV)",
                                       data=csv,
                                       file_name=f"{ticker_input}_full_price_history.csv",
                                       mime="text/csv",
                                       key="download_full_history")
                else:
                    st.info(f"Không có dữ liệu lịch sử giá cho {ticker_input}")

# Sidebar thông tin mô tả
st.sidebar.markdown("---")
st.sidebar.info("""
Tải dữ liệu có thể mất vài giây  
Dữ liệu được lấy từ TCBS và VCI  
Liên hệ: 0962677528
""")
