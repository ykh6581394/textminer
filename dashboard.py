# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 09:10:17 2024

@author: 유국현
"""

import streamlit as st
import io
import os
import zipfile
import pandas as pd
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')
from selenium import webdriver
from  selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
from bs4 import BeautifulSoup
from webdriver_manager.firefox import GeckoDriverManager

from wordcloud import WordCloud
import konlpy
from matplotlib import pyplot as plt
from matplotlib import font_manager as fm


from gensim.models import Word2Vec
import networkx as nx
from matplotlib import rc



def oneLenFiter(nouns_1):
    filtered = []
    
    for ii in range(len(nouns_1)):
        dt = []
        nouns_unit = nouns_1[ii]
        for jj in range(len(nouns_unit)):
            if len(nouns_unit[jj]) >1:
                dt.append(nouns_unit[jj])
        filtered.append(dt)
    return filtered

st.title("Reply Crawler")

def youtubeReplyCrawler(url, api_key, path):
    comments = list()
    api_obj = build('youtube', 'v3', developerKey=api_key)
    
    videoid = url.split("=")[-1]
    
    response = api_obj.commentThreads().list(part='snippet,replies', videoId=videoid,maxResults=10000).execute()
    
    
    while response:
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append([comment['textDisplay'], comment['authorDisplayName'], comment['publishedAt'], comment['likeCount']])
     
            if item['snippet']['totalReplyCount'] > 0:
                for reply_item in item['replies']['comments']:
                    reply = reply_item['snippet']
                    comments.append([reply['textDisplay'], reply['authorDisplayName'], reply['publishedAt'], reply['likeCount']])
     
        if 'nextPageToken' in response:
            response = api_obj.commentThreads().list(part='snippet,replies', videoId=videoid, pageToken=response['nextPageToken'], maxResults=100).execute()
        else:
            break
    col = ['comment', 'author', 'date', 'num_likes']
    df = pd.DataFrame(comments, columns=col)

    return df
    #df.to_csv(directory+'/'+path+'/'+file_name+'.csv', index=None)
    
def getNavernewsReply(url, num , path, wait_time=5, delay_time=0.1):
    def installff():
        os.system('sbase install geckodriver')
        os.system('ln -s /home/appuser/venv/lib/python3.7/site-packages/seleniumbase/drivers/geckodriver /home/appuser/venv/bin/geckodriver')

    _ = installff()
    service = Service(GeckoDriverManager().install())
    options = Options() 
    options.add_argument("--headless=new")
    #options.binary_location = 'C:/Program Files/Mozilla Firefox/firefox.exe'

    driver = webdriver.Firefox(options=options, service=service)
    driver.implicitly_wait(wait_time)
    driver.get(url)
    
    while True:
        try:
            more  =  driver.find_element(By.CLASS_NAME,  'u_cbox_btn_more')
            more.click()
            time.sleep(delay_time)

        except:
            break
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    nicknames = soup.select('span.u_cbox_nick')
    list_nicknames = [nickname.text for nickname in nicknames]

    datetimes = soup.select('span.u_cbox_date')
    list_datetimes = [datetime.text for datetime in datetimes]

    contents = soup.select('span.u_cbox_contents') 
    list_contents = [content.text for content in contents]


    list_sum = list(zip(list_nicknames,list_datetimes,list_contents))

    driver.quit()
    col = ['작성자','시간','내용']

    df = pd.DataFrame(list_sum, columns=col)
    return df
    #df.to_csv(directory+'/'+path+'/'+'naver_'+str(num)+'.csv')

@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8-sig')
    
tab1, tab2, tab3, tab4 = st.tabs(["You tube", "Naver", "URL All", "Analysis"])

with tab1:
    url_you = st.text_input("Youtube Link")
    api_you = st.text_input("API Key")
    videoid = url_you.split("=")[-1]

    if st.button("Crawl Youtube"):
        with st.spinner('Wait for it...'):
            df = youtubeReplyCrawler(url_you, api_you, "youtube")
        st.success('Done!')
        csv = convert_df(df)
        st.download_button(
            "Press Download",
            csv,
            videoid + ".csv",
            key="download_csv")


with tab2:
    url_naver = st.text_input("Naver Reply Link")
    num       = st.text_input("Comment")
    
    if st.button("Crawl Naver News Reply"):
        with st.spinner('Wait for it...'):
            df = getNavernewsReply(url_naver, num, "naver", wait_time=5, delay_time=0.1)
        st.success('Done!')
        csv = convert_df(df)
        st.download_button(
            "Press Download",
            csv,
            "naver_"+str(num) + ".csv",
            key="download_csv")

with tab3:

    api_yous = st.text_input("You Tube API Key")
    uploaded_files_url =  st.file_uploader("Upload your urls",type=['csv'],accept_multiple_files=False)
    
    if st.button("Crawl All Reply"):
        urls_all = pd.read_csv(uploaded_files_url)
        
        sel_url = urls_all["urls"]
        
        buf = io.BytesIO()
        with zipfile.ZipFile(buf,"x") as csv_zip:
            progress_text = "Now calculating"
            my_bar = st.progress(0.0, text=progress_text)
            for k in range(len(sel_url)):
                time.sleep(0.02)
                my_bar.progress(100*(k+1)//len(sel_url))
                if "youtube" in sel_url[k]:
                    url_you = sel_url[k]
                    df = youtubeReplyCrawler(url_you, api_yous, "all")
                    videoid = url_you.split("=")[-1]
                    csv_zip.writestr(videoid + ".csv",df.to_csv(index=False).encode('utf-8-sig'))
                    
                elif "naver" in sel_url[k]:
                    url_naver = sel_url[k]
                    df = getNavernewsReply(url_naver, k, "all", wait_time=5, delay_time=0.1)
                    csv = convert_df(df)
                    csv_zip.writestr("naver_"+str(k) + ".csv",df.to_csv(index=False).encode('utf-8-sig'))



        st.download_button(
                        label = "Download zip",
                        data = buf.getvalue(),
                        file_name = "mydownload.zip"
                        )
        st.balloons()
                
      

with tab4:
    uploaded_files_csv =  st.file_uploader("Upload your reply csv",type=['csv'],accept_multiple_files=True)
    sel_data = st.text_input("Select Top N (Only Network Analysis")
    progress_text = "Now Load Reply"
    my_bar2 = st.progress(0.0, text=progress_text)
    plt.rcParams["font.family"] = os.path.join(os.getcwd(), "Gothic_A1/GothicA1-Light.ttf")
    #fpath = os.path.join(os.getcwd(), "Gothic_A1/GothicA1-Light.ttf")
    #prop = fm.FontProperties(fname=fpath)
    
    
    path_all = uploaded_files_csv
    df = pd.DataFrame()
    each_len = []
    for idx in range(len(path_all)):
        my_bar2.progress(100*(idx+1)//len(path_all))
        df_unit = pd.read_csv(path_all[idx])
        each_len.append(len(df_unit))
        df = pd.concat([df, df_unit], ignore_index = True)
        
    if st.button("Summarizing All Reply"):
        
        st.table(df.head(5))
        st.write("All Data Length : "+str(len(df)))
        st.write(each_len)
            
    if st.button("WordCloud"):
        with st.spinner("Now Make Wordcloud"):
                
            kkma = konlpy.tag.Kkma() 
            
            text = df["comment"].str.replace('[^가-힣]', ' ', regex = True)
            
            nouns = text.apply(kkma.nouns)
            
            nouns = nouns.explode()
            
            df_word = pd.DataFrame({'word' : nouns})
            df_word['count'] = df_word['word'].str.len()
            df_word = df_word.query('count >= 2')
            
            df_word = df_word.groupby('word', as_index = False).count().sort_values('count', ascending = False)
            dic_word = df_word.set_index('word').to_dict()['count']
            
            wc = WordCloud(random_state = 123, font_path = 'malgun', width = 400,
                           height = 400, max_font_size = 150, background_color = 'white',colormap='inferno')
            
            img_wordcloud = wc.generate_from_frequencies(dic_word)
            
            fig = plt.figure(figsize = (15, 15)) # 크기 지정하기
            plt.axis('off') # 축 없애기
            plt.imshow(img_wordcloud) # 결과 보여주기
            plt.show()
            st.pyplot(fig)
            
            csv1 = convert_df(df_word)
            st.download_button(
                "Press Wordcloud Download",
                csv1,
                "wordcloud.csv",
                key="download_csv")

    if st.button("Network Analysis"):
        
        with st.spinner("Now Make Word Relations"):
            
                
            kkma = konlpy.tag.Kkma() 
            
            text = df["comment"].str.replace('[^가-힣]', ' ', regex = True)
            
            nouns = text.apply(kkma.nouns)
            nouns_1 = nouns
            nouns = nouns.explode()
        
            nouns_2 = oneLenFiter(nouns_1)
                        
            df_word = pd.DataFrame({'word' : nouns})
            df_word['count'] = df_word['word'].str.len()
            df_word = df_word.query('count >= 2')
            
            df_word = df_word.groupby('word', as_index = False).count().sort_values('count', ascending = False)
                                    
            model = Word2Vec(sentences=nouns_2 ,  window = 5, min_count=5 , workers = 4 , sg = 0)
            word_uniq = list(df_word["word"])
            
            progress_text3 = "Now Make Weight"
            my_bar3 = st.progress(0.0, text=progress_text3)
            
                        
                        
            edge1 = []
            edge2 = []
            weight = []
            tt=0
            for j in word_uniq:
                my_bar3.progress(100*(tt+1)//len(word_uniq))
                tt=tt+1
                for k in word_uniq:
                    try:
                        if j>k:
                            weight_unit = model.wv.similarity(j,k)
                            edge1.append(j)
                            edge2.append(k)
                            weight.append(weight_unit)
                    except:
                        continue
                
                    
            df = pd.DataFrame({"source":edge1, "target":edge2, "weight":weight})

            
            df = df.sort_values('weight',ascending=False)
            
            G=nx.Graph()
            
            
            sel = int(sel_data) # len(df)
            
            for i in range(sel):
                df_unit = df.iloc[i]
                node1, node2 = df_unit['source'], df_unit['target']
                weight = df_unit["weight"]
                G.add_edge(node1,node2,weight=weight)
            
   
    
            pos = nx.spring_layout(G, k=0.2)
            fig1 = plt.figure(figsize=(12,8))
            nx.draw_networkx(G, pos,
                             node_size = 10,
                             node_color = "green",
                             alpha=.8,
                             font_size=18
                             )
            plt.show()
            st.pyplot(fig1)  
            
            
            csv2 = convert_df(df)
            st.download_button(
                "Press Network Download",
                csv2,
                "wordnetwork.csv",
                key="download_csv")



    
    
    