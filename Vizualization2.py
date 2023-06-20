#!/usr/bin/env python
# coding: utf-8

# In[74]:

import pandas as pd
import numpy as np
import time
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# In[25]:
def mae(y_true, y_pred):
    n = len(np.array(y_true))
    error_sum = 0.0
    for i in range(n):
        error_sum += abs(np.array(y_true)[i] - np.array(y_pred)[i])
    mae = error_sum / n
    return mae


def r2_score(y_true, y_pred):
    mean_y_true = np.mean(y_true)
    ssr = np.sum((np.array(y_true) - np.array(y_pred)) ** 2)
    sst = np.sum((np.array(y_true) - np.array(mean_y_true)) ** 2)
    r2 = 1 - (ssr / sst)
    return r2



station = pd.read_csv('최종_station_list.csv')
xy= pd.read_excel('서울교통공사_역사정보_20220530.xlsx')

start_date = datetime.strptime('2022-12-22', '%Y-%m-%d').date()
numdays = 10
dates = [start_date + timedelta(days=x) for x in range(numdays)]

# In[48]:


station['역명']=0
for i in range(0,256):
    station['역명'][i]=station['0'][i].split("_")[1]


# In[40]:


xy_re = xy.iloc[2:,:]
xy_ree=xy_re[['Unnamed: 5','Unnamed: 16','Unnamed: 17']]
xy_ree.columns=['역명','경도','위도']
xy_ree=xy_ree.iloc[2:].reset_index(drop=True)


# In[52]:


lon_rat = xy_ree[xy_ree['역명'].isin(station['역명'].values)].reset_index(drop=True)


# In[56]:


y_test = np.load('y_test.npy')
per_day_client = np.load('per_day_client.npy')
per_day_profit = np.load('per_day_profit.npy')
predictions = np.load('predictions.npy')
temp = predictions.reshape(10,10,256*256)

min = np.load('min.npy')
max = np.load('max.npy')
mean = np.load('mean.npy')


# In[63]:

des = station['0']

# # Dash Board set up

# In[ ]:

st.set_page_config(
    page_title="Subway charge optimazation",
    page_icon="✅",
    layout="wide",
)
st.title('Subway charge optimazation')
col1,col2 = st.columns([3,2])
# 공간을 2:3 으로 분할하여 col1과 col2라는 이름을 가진 컬럼을 생성합니다.  

st.sidebar.title('Subway scenario🚇')
option1 = st.sidebar.selectbox(
        "📅출발 날짜를 고르세요",
        (dates))
option2 = st.sidebar.selectbox(
        "🕟출발 시간대를 고르세요",
        (['05-07시간대','07-09시간대','09-11시간대','11-13시간대','13-15시간대','15-17시간대','17-19시간대','19-21시간대','21-23시간대','23시이후']))
option3 = st.sidebar.selectbox(
        "🧳출발지를 고르세요",
        (des))
option4 = st.sidebar.selectbox(
        "🗻목적지를 고르세요",
        (des))
radio_select =st.sidebar.radio(
    "💳지하철 기본 요금을 고르세요",
    ['1290원','1350원','1400원','1450원','1500원','1550원','1600원'],
    horizontal=True
    )
chk_all = st.sidebar.checkbox("전체 혼잡도 보기")
# 필터 적용버튼 생성 
start_button = st.sidebar.button(
     "분석 시작 📊 "#"버튼에 표시될 내용"
)
#with col1 :
  # column 1 에 담을 내용
    #st.header('Movement visualization')

#with col2 :
    # column 2 에 담을 내용
    #st.header('Dynamic pricing scenario')

if start_button:
    with col1 :
        st.write('📅2022-12-22 ~ 2022.12.31까지 🕟10가지 시간대, 🧳256가지 출발역 및 도착역의 혼잡도를 예측했습니다.')
        st.write('예상 혼잡도를 바탕으로 혼잡도가 높으면 요금이 올라가는 Dynamic Pricing을 구현했고 Back-Test 결과를 시각화 했습니다.')
        st.write(" ")
        date_idx = dates.index(option1)
        temporal = predictions[date_idx]
        real_temp = y_test[date_idx]
        timed = ['05-07시간대','07-09시간대','09-11시간대','11-13시간대','13-15시간대','15-17시간대','17-19시간대','19-21시간대','21-23시간대','23시이후'].index(option2)
        conge=[]
        real=[]
        for time in range(0,10):
            conge.append(temporal[time][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)])
            real.append(real_temp[time][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)])
        r2 = r2_score(real, conge)
        congestion = temporal[timed][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)]
        real_con = real_temp[timed][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)]
        mae_score = mae([real_con], [congestion])
        if congestion<np.quantile(predictions,0.25):
            d_con = '여유'
        elif congestion<np.quantile(predictions,0.5) and congestion>=np.quantile(predictions,0.25):
            d_con= '보통'
        elif congestion<np.quantile(predictions,0.75) and congestion>=np.quantile(predictions,0.5):
            d_con='주의'
        else:
            d_con='혼잡'
        if not chk_all:
            st.subheader(f'선택한 시간대의 목적지까지 예상 혼잡도는 :red[{d_con}({round(congestion*100,1)}%)]입니다(MAE:{round(mae_score,3)}).')
            st.write('※MAE(평균절대오차): 예측 값과 실제 값 간의 차이를 계산하는 데 사용되는 평가 지표')
        else:
            congestion3=[]
            real_con2 = []
            for time in range(10):
                congestion3.append(predictions[date_idx][time][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)])
                real_con2.append(y_test[date_idx][time][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)])
            conge2 = np.mean(congestion3)
            real2 = np.mean(real_con2)
            if conge2<np.quantile(predictions,0.25):
                d_con = '여유'
            elif conge2<np.quantile(predictions,0.5) and conge2>=np.quantile(predictions,0.25):
                d_con= '보통'
            elif conge2<np.quantile(predictions,0.75) and conge2>=np.quantile(predictions,0.5):
                d_con='주의'
            else:
                d_con='혼잡'
            mae_score2 = mae([real2], [conge2])
            st.subheader(f'선택한 시간대의 목적지까지 예상 혼잡도는 :red[{d_con}({round(conge2*100,1)}%)]입니다(MAE:{round(mae_score,3)}).')
            st.write('※MAE(평균절대오차): 예측 값과 실제 값 간의 차이를 계산하는 데 사용되는 평가 지표')
        start = lon_rat[lon_rat['역명']==option3.split("_")[1]][['위도','경도']]
        end = lon_rat[lon_rat['역명']==option4.split("_")[1]][['위도','경도']]
        con = pd.concat([start,end],axis=0)
        con.columns=['lat','lon']
        st.markdown('☆출발역 / 목적지역 좌표')
        st.map(con)
        st.write(" ")
        trans = pd.DataFrame(conge,
                     index=['05-07시간대','07-09시간대','09-11시간대','11-13시간대','13-15시간대','15-17시간대','17-19시간대','19-21시간대','21-23시간대','23시이후'],columns=['혼잡도(%)'])
        
        
        if not chk_all:
            st.subheader(f'{option1}일 {option3}에서 {option4}까지 시간대 별 혼잡도(설명력: :blue[{round(r2*100,1)}%])')
            st.write('※설명력(r2_score):예측 값과 실제 값 간의 상관 관계를 나타내는 값으로, 모델이 얼마나 잘 데이터를 설명하고 예측하는지를 측정합니다. 0과 1 사이의 값을 가지며, 1에 가까울수록 모델의 예측 성능이 좋다는 의미입니다.')
            st.area_chart(trans)
        else:
            viz_all=[]
            real_fd=[]
            for day in range(0,10):
                for time in range(0,10):
                    viz_all.append(predictions[day][time][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)])
                    real_fd.append(y_test[day][time][list(station['0'].values).index(option3)][list(station['0'].values).index(option4)])
            r22 = r2_score(np.array(real_fd).flatten(),np.array(viz_all).flatten())
            viz_all2 = np.array(viz_all).reshape(10,10)
            viz_all2 = pd.DataFrame(viz_all2,columns=dates,index=['05-07시간대','07-09시간대','09-11시간대','11-13시간대','13-15시간대','15-17시간대','17-19시간대','19-21시간대','21-23시간대','23시이후']).T
            st.subheader(f'{option1}일 {option3}에서 {option4}까지 시간대 별 혼잡도(설명력: :blue[{round(r22*100,1)}%])')
            st.write('※설명력(r2_score):예측 값과 실제 값 간의 상관 관계를 나타내는 값으로, 모델이 얼마나 잘 데이터를 설명하고 예측하는지를 측정합니다. 0과 1 사이의 값을 가지며, 1에 가까울수록 모델의 예측 성능이 좋다는 의미입니다.')
            st.line_chart(viz_all2)

        
            
    with col2 :
        st.subheader(':red[Dynamic Pricing 시나리오]')
        see_data = st.expander('Raw data를 먼저 살펴보려면 👉')
        with see_data:
            st.dataframe(pd.DataFrame(predictions[date_idx][timed],columns=station['0'].values,index=station['0'].values))
        pd.options.display.float_format = '{: .1f}'.format
        st.write(f'▲비교대상: 기본 요금 {radio_select}의 일괄 적용')
        f, e= st.columns([0.5,10])
        with e:
            st.text(f"     "+'▲지하철 수요 탄력성은 -0.283이라는 가정 하에 기본 요금 1250원에서 변하는 수요량과 매출액을 추정')
        st.subheader('Dynamic Pricing 결과')
        base=[1968,2156,2386,2423,2556,2678,2450]
        C=[687.7,819.3,1003,989.4,1073,1146,864.2]
        charge_idx = ['1290원','1350원','1400원','1450원','1500원','1550원','1600원'].index(radio_select)
        min_v=min[charge_idx][date_idx][timed]
        max_v=max[charge_idx][date_idx][timed]
        mean_v=mean[charge_idx][date_idx][timed]
        perday_C=per_day_client[charge_idx][date_idx][timed] / 100
        perday_P=per_day_profit[charge_idx][date_idx][timed] / 1000000

        min_v2=np.min(min[charge_idx])
        max_v2=np.max(max[charge_idx])
        mean_v2=np.mean(mean[charge_idx])
        perday_C2=np.sum(per_day_client[charge_idx]) / 100
        perday_P2=np.sum(per_day_profit[charge_idx]) / 1000000
        col3,col4,col5,col6,col7 = st.columns([1,1,1,1,1])
        if not chk_all: 
            with col3:
                st.metric(label="Min Charge", value=min_v, delta=min_v-1250,
                delta_color="inverse")
            with col4:
                st.metric(label="Max Charge", value=max_v, delta=max_v-1250,
                delta_color="inverse")
            with col5:
                st.metric(label="Mean Charge", value=round(mean_v,-1), delta=np.ceil(mean_v-1250),
                delta_color="inverse")
            with col6:
                st.metric(label="per_day_client(백명)", value=round(perday_C,1))
            with col7:
                st.metric(label="per_day_profit(백만원)", value=round(perday_P,1))
            front, end= st.columns([0.5,10])
            with end:
                st.write(f'△Min,Max,Mean은 각각 Dynamic Pricing의 최저, 최고, 평균 값을 나타냅니다.')
                st.write(f'△per_day_client는 {radio_select} 일괄 적용과 비교하여 하루에 변화된 지하철 수요')
                st.write(f'△per_day_profit은 {radio_select} 일괄적용과 비교하여 하루에 벌어들이는 매출액')
        else:
            st.write('※per_day_client와 per_day_profit은 2022-12-22 ~ 2022-12-31까지 합계')
            with col3:
                st.metric(label="Min Charge", value=min_v2, delta=min_v-1250,
                delta_color="inverse")
            with col4:
                st.metric(label="Max Charge", value=max_v2, delta=max_v-1250,
                delta_color="inverse")
            with col5:
                st.metric(label="Mean Charge", value=round(mean_v2,-1), delta=np.ceil(mean_v2-1250),
                delta_color="inverse")
            with col6:
                st.metric(label="per_day_client(백명)", value=round(perday_C2,1))
            with col7:
                st.metric(label="per_day_profit(백만원)", value=round(perday_P2,1))
            front, end= st.columns([0.5,10])
            with end:
                st.write(f'△Min,Max,Mean은 각각 Dynamic Pricing의 최저, 최고, 평균 값을 나타냅니다.')
                st.write(f'△per_day_client는 {radio_select} 일괄 적용과 비교하여 하루에 변화된 지하철 수요')
                st.write(f'△per_day_profit은 {radio_select} 일괄 적용과 비교하여 하루에 벌어들이는 매출액')
        st.write(" ")
        st.write(" ")
        st.subheader('Dynamic Pricing 구간')
        st.write('◇혼잡도 구간마다 변하는 요금을 확인할 수 있습니다.')
        plt.style.use(['dark_background'])
        #plt.rcParams['font.family'] = 'Malgun Gothic'
        fig = plt.figure(figsize=(5,2))
        plt.fill_between(sorted(temp[0].flatten()),base[charge_idx]-C[charge_idx]*(np.cos(sorted(temp[0].flatten()))))
        plt.ylim(1000, 2000)
        st.pyplot(fig,use_container_width=False)
