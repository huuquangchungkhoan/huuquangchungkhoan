import streamlit as st
import pandas as pd
from vnstock import Vnstock
from datetime import datetime, timedelta
import time
import re
import random
import warnings

# Tắt cảnh báo
warnings.filterwarnings("ignore")

# Cấu hình trang
st.set_page_config(
    page_title="Hữu Quang Chứng Khoán", 
    layout="wide",
    page_icon="📊"
)

# CSS cho giao diện
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: white;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(to right, #8B0000, #FF0000);
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .dataframe {
        font-size: 14px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px;
        padding: 10px 16px;
        background-color: #0E1117;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF0000;
    }
    .waiting {
        padding: 10px;
        background-color: #FFF3CD;
        color: #856404; 
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Tiêu đề
st.markdown('<h1 class="main-header">Hữu Quang Chứng Khoán</h1>', unsafe_allow_html=True)
st.markdown('<h2 class="sub-header">Ứng dụng Tra cứu Tin tức</h2>', unsafe_allow_html=True)

# Tạo tabs
tab1, tab2 = st.tabs(["Tin tức", "Tải nhiều mã"])

# Sidebar: cài đặt và tùy chọn người dùng
st.sidebar.header("Tùy chọn")

# Nhập mã cổ phiếu
ticker_input = st.sidebar.text_input("Nhập mã cổ phiếu:", "VGT")

# Chọn khoảng thời gian
st.sidebar.subheader("Khoảng thời gian")
end_date = datetime.now()
start_date = datetime(2015, 1, 1)  # Mặc định từ 2015
start_date_input = st.sidebar.date_input("Từ ngày:", start_date)
end_date_input = st.sidebar.date_input("Đến ngày:", end_date)

# Đặt mặc định là 5000 tin tức
max_records = st.sidebar.slider("Số lượng tin tức tối đa:", 10, 5000, 5000)

# Phần lọc từ khóa tùy chỉnh
st.sidebar.subheader("Lọc từ khóa")
custom_filter = st.sidebar.text_area("Thêm từ khóa lọc (mỗi từ một dòng):", height=100)
custom_filter_list = [x.strip() for x in custom_filter.split('\n') if x.strip()]

# Danh sách các cụm từ cần lọc bỏ mặc định
default_unwanted_phrases = [
    'giá tăng liên tiếp', 'dấu hiệu bán chủ động', 'dấu hiệu mua chủ động',
    'dấu hiệu đè giá', 'dấu hiệu đẩy giá', 'khối lượng tăng liên tiếp',
    'khớp lệnh đột biến', 'vượt đường ngắn hạn', 'giá giảm liên tiếp',
    'lệnh mua đột biến', 'lệnh bán đột biến', 'khối lượng giao dịch',
    'đường ngắn hạn', 'đường già hạn', 'ma100', 'ma20', 'ma200', 'ma50', 'phá đỉnh',
    'vượt đường', 'phá đáy', 'khối lượng', 'thanh khoản',
    'trụ vững', 'hồi phục', 'điều chỉnh', 'giao dịch lớn',
    'đảo chiều', 'xu hướng', 'ma trung hạn', 'ma dài hạn',
    'thân nến', 'nến đảo chiều', 'nến búa', 'nến sao', 'nến doji',
    'rsi', 'macd', 'stochastic', 'bollinger', 'ichimoku', 'fibonacci'
]

# Kết hợp danh sách mặc định và tùy chỉnh
unwanted_phrases = default_unwanted_phrases + custom_filter_list

# Hàm lấy tin tức với cơ chế retry khi gặp rate limit
def get_company_news_with_retry(symbol, page, page_size=100, max_retries=5):
    retries = 0
    wait_message = st.empty()
    
    while retries <= max_retries:
        try:
            # Tạo đối tượng stock mới cho mỗi lần gọi
            stock = Vnstock().stock(symbol=symbol, source='TCBS')
            news_page = stock.company.news(page=page, page_size=page_size)
            wait_message.empty()
            return news_page
        except Exception as e:
            error_msg = str(e)
            # Kiểm tra nếu là lỗi rate limit
            if "quá nhiều request" in error_msg.lower():
                # Trích xuất thời gian chờ từ thông báo lỗi
                wait_time_match = re.search(r'sau (\d+)', error_msg)
                if wait_time_match:
                    wait_time = int(wait_time_match.group(1)) + 5  # Thêm 5 giây phòng hờ
                else:
                    wait_time = (2 ** retries) + 20  # Exponential backoff
                
                # Hiển thị đếm ngược 
                wait_message.markdown(f"<div class='waiting'>Chờ {wait_time} giây do vượt giới hạn API...</div>", unsafe_allow_html=True)
                time.sleep(wait_time)
                
                retries += 1
            else:
                # Nếu không phải lỗi rate limit, đợi ít hơn
                wait_time = 3
                wait_message.warning(f"Lỗi: {error_msg}. Thử lại sau {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
                
            if retries > max_retries:
                wait_message.error(f"Đã thử lại {max_retries} lần không thành công. Bỏ qua.")
                return pd.DataFrame()
    
    return pd.DataFrame()

# Hàm lọc tin tức
def filter_news(news_df, start_date_pd, end_date_pd, unwanted_phrases):
    if news_df.empty:
        return news_df, 0
    
    # Tạo bản sao để tránh lỗi
    df = news_df.copy()
    
    # Lọc từ khóa
    filter_condition = ~df['title'].str.lower().str.contains('|'.join(unwanted_phrases), case=False, na=False)
    filtered_df = df[filter_condition].copy()
    removed_count = len(df) - len(filtered_df)
    
    # Chuyển đổi ngày tháng
    if 'publish_date' in filtered_df.columns:
        filtered_df['publish_date'] = pd.to_datetime(filtered_df['publish_date'])
        
        # Lọc theo ngày
        filtered_df = filtered_df[(filtered_df['publish_date'] >= start_date_pd) & 
                              (filtered_df['publish_date'] <= end_date_pd)].copy()
    
    return filtered_df, removed_count

# Tab Tin tức - hiển thị dần dần
with tab1:
    st.header(f"Tin tức của cổ phiếu {ticker_input}")
    
    # Khởi tạo các placeholder để hiển thị dữ liệu
    data_container = st.empty()
    status_container = st.empty()
    progress_container = st.empty()
    download_container = st.empty()
    
    # Chuẩn bị dữ liệu ngày tháng
    start_date_pd = pd.to_datetime(start_date_input)
    end_date_pd = pd.to_datetime(end_date_input)
    
    if ticker_input:
        # Khởi tạo
        all_news = pd.DataFrame()
        filtered_df_final = pd.DataFrame()
        page = 0
        continue_loading = True
        total_removed = 0
        
        # Hiển thị thanh tiến độ
        progress_bar = progress_container.progress(0)
        
        # Chạy vòng lặp tải dữ liệu và hiển thị tức thì
        while continue_loading and len(all_news) < max_records:
            # Hiển thị trạng thái
            status_container.text(f"Đang tải trang {page+1}...")
            
            # Lấy dữ liệu từng trang
            news_page = get_company_news_with_retry(ticker_input, page)
            
            if news_page.empty:
                status_container.text("Đã tải hết tin tức.")
                break
            
            # Thêm vào dataframe tổng
            all_news = pd.concat([all_news, news_page], ignore_index=True)
            
            # Lọc dữ liệu mới nhận
            temp_filtered, removed = filter_news(all_news, start_date_pd, end_date_pd, unwanted_phrases)
            total_removed = removed
            
            # Định dạng ngày tháng nếu có
            if 'publish_date' in temp_filtered.columns:
                # Sắp xếp theo thời gian mới nhất trước
                temp_filtered = temp_filtered.sort_values('publish_date', ascending=False)
                
                # Định dạng hiển thị
                display_df = temp_filtered.copy()
                display_df['publish_date'] = display_df['publish_date'].dt.strftime('%d/%m/%Y %H:%M')
                
                # Sắp xếp lại thứ tự cột
                if 'title' in display_df.columns:
                    first_cols = ['publish_date', 'title']
                    other_cols = [col for col in display_df.columns if col not in first_cols]
                    display_df = display_df[first_cols + other_cols]
                
                # Hiển thị dataframe
                data_container.dataframe(display_df, use_container_width=True)
                
                # Lưu lại dataframe cuối cùng để download
                filtered_df_final = display_df
            
            # Cập nhật thanh tiến độ
            progress = min(len(all_news) / max_records, 1.0)
            progress_bar.progress(progress)
            
            # Cập nhật thông tin
            status_container.text(f"Đã tải: {len(all_news)} tin tức | Hiển thị: {len(temp_filtered)} tin tức (đã lọc {total_removed} tin kỹ thuật)")
            
            # Tăng trang và đợi để tránh rate limit
            page += 1
            time.sleep(random.uniform(2.0, 3.0))
            
            # Kiểm tra nếu đã đủ số lượng
            if len(all_news) >= max_records:
                status_container.text(f"Đã đạt giới hạn {max_records} tin tức.")
                break
        
        # Hiển thị nút tải xuống khi có dữ liệu
        if not filtered_df_final.empty:
            csv = filtered_df_final.to_csv(index=False).encode("utf-8-sig")
            download_container.download_button(
                label=f"Tải xuống {len(filtered_df_final)} tin tức (CSV)",
                data=csv,
                file_name=f"{ticker_input}_news.csv",
                mime="text/csv"
            )
    else:
        st.info("Vui lòng nhập mã cổ phiếu để tìm kiếm tin tức.")

# Tab Tải nhiều mã
with tab2:
    st.header("Tải tin tức nhiều mã cổ phiếu")
    
    # Nhập danh sách mã cổ phiếu
    multi_tickers = st.text_area(
        "Nhập danh sách mã cổ phiếu (tối đa 10 mã, mỗi mã một dòng):",
        value="VGT\nPVS\nVND\nSSI",
        height=150
    )
    
    # Chuyển đổi thành danh sách
    ticker_list = [ticker.strip().upper() for ticker in multi_tickers.split('\n') if ticker.strip()]
    
    # Giới hạn tối đa 10 mã
    if len(ticker_list) > 10:
        st.warning("Chỉ có thể tải tối đa 10 mã cổ phiếu. Chỉ 10 mã đầu tiên sẽ được xử lý.")
        ticker_list = ticker_list[:10]
    
    # Hiển thị danh sách các mã sẽ được tải
    st.write(f"Các mã sẽ được tải: {', '.join(ticker_list)}")
    
    # Số lượng tin tức tối đa cho mỗi mã
    news_per_ticker = st.slider("Số tin tức tối đa cho mỗi mã:", 10, 5000, 1000)
    
    # Tùy chọn xử lý tuần tự để tránh rate limit
    process_sequentially = st.checkbox("Xử lý tuần tự để giảm lỗi API limit", value=True, 
                                   help="Xử lý từng mã một, chậm hơn nhưng ít bị lỗi giới hạn API hơn")
    
    # Cảnh báo
    st.warning("LƯU Ý: Quá trình tải có thể mất nhiều thời gian vì giới hạn API. Ứng dụng sẽ tự động chờ khi bị giới hạn.")
    
    # Nút tải xuống
    if st.button("Bắt đầu tải tin tức"):
        if ticker_list:
            # DataFrame để lưu tất cả tin tức
            all_news = pd.DataFrame()
            
            # Hiển thị tiến trình tổng thể
            progress_text = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Chuẩn bị dữ liệu ngày tháng cho lọc
            start_date_pd = pd.to_datetime(start_date_input)
            end_date_pd = pd.to_datetime(end_date_input)
            
            # Thống kê
            total_processed = 0
            total_news_count = 0
            
            # Lặp qua từng mã cổ phiếu
            for i, ticker in enumerate(ticker_list):
                progress_text.text(f"Đang xử lý: {ticker} ({i+1}/{len(ticker_list)})")
                
                # Lấy tin tức cho từng mã
                try:
                    # Lấy tin từng mã riêng biệt
                    ticker_news = pd.DataFrame()
                    page = 0
                    
                    while len(ticker_news) < news_per_ticker:
                        status_text.text(f"Đang tải trang {page+1} cho {ticker}...")
                        
                        # Sử dụng hàm với retry để tránh lỗi rate limit
                        news_page = get_company_news_with_retry(ticker, page)
                        
                        if news_page.empty or len(news_page) == 0:
                            break
                        
                        ticker_news = pd.concat([ticker_news, news_page], ignore_index=True)
                        status_text.text(f"Đã tải {len(ticker_news)} tin cho {ticker}...")
                        
                        # Tăng số trang
                        page += 1
                        
                        # Tạm dừng để tránh rate limit
                        time.sleep(random.uniform(2.5, 4.0))
                        
                        # Nếu đã đủ số lượng tin, dừng lại
                        if len(ticker_news) >= news_per_ticker:
                            ticker_news = ticker_news.head(news_per_ticker)
                            break
                    
                    # Thêm cột mã chứng khoán
                    if not ticker_news.empty:
                        # Thêm cột symbol
                        ticker_news['symbol'] = ticker
                        
                        # Lọc theo từ khóa
                        filter_condition = ~ticker_news['title'].str.lower().str.contains('|'.join(unwanted_phrases), case=False, na=False)
                        filtered_ticker_news = ticker_news[filter_condition].copy()
                        
                        # Lọc theo thời gian
                        if 'publish_date' in filtered_ticker_news.columns:
                            filtered_ticker_news['publish_date'] = pd.to_datetime(filtered_ticker_news['publish_date'])
                            filtered_ticker_news = filtered_ticker_news[(filtered_ticker_news['publish_date'] >= start_date_pd) & 
                                                                     (filtered_ticker_news['publish_date'] <= end_date_pd)]
                            
                            # Định dạng ngày tháng
                            filtered_ticker_news['publish_date'] = filtered_ticker_news['publish_date'].dt.strftime('%d/%m/%Y %H:%M')
                        
                        # Thêm vào kết quả chung
                        all_news = pd.concat([all_news, filtered_ticker_news], ignore_index=True)
                        
                        # Thống kê
                        status_text.text(f"Hoàn thành {ticker}: Lọc được {len(filtered_ticker_news)}/{len(ticker_news)} tin")
                except Exception as e:
                    status_text.error(f"Lỗi khi xử lý {ticker}: {str(e)}")
                
                # Cập nhật tiến trình
                total_processed += 1
                progress_bar.progress(total_processed / len(ticker_list))
                
                # Nghỉ giữa các mã để tránh rate limit
                if i < len(ticker_list) - 1 and process_sequentially:
                    wait_time = random.randint(7, 15)  # Nghỉ dài hơn giữa các mã
                    for remaining in range(wait_time, 0, -1):
                        status_text.text(f"Đã hoàn thành {ticker}. Đợi {remaining}s trước khi xử lý mã tiếp theo...")
                        time.sleep(1)
            
            # Sắp xếp lại thứ tự cột
            if not all_news.empty:
                # Sắp xếp theo thời gian và symbol
                if 'publish_date' in all_news.columns and 'title' in all_news.columns and 'symbol' in all_news.columns:
                    first_cols = ['publish_date', 'title', 'symbol']
                    other_cols = [col for col in all_news.columns if col not in first_cols]
                    all_news = all_news[first_cols + other_cols]
                
                # Hiển thị thông báo hoàn thành
                progress_text.text(f"Đã hoàn thành tải dữ liệu cho {len(ticker_list)} mã cổ phiếu")
                status_text.text(f"Tổng số tin tức đã tải: {len(all_news)}")
                
                # Nút tải xuống CSV
                csv = all_news.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label=f"Tải xuống tất cả {len(all_news)} tin tức (CSV)",
                    data=csv,
                    file_name=f"tin_tuc_{len(ticker_list)}_ma_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Không tìm thấy tin tức nào cho các mã đã chọn")
        else:
            st.warning("Vui lòng nhập ít nhất một mã cổ phiếu")

# Thông tin sidebar
st.sidebar.markdown("---")
st.sidebar.info("Chứng Khoán Hữu Quang, Liên hệ: 0962677528")
