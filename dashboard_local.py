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
from io import BytesIO
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')
from selenium import webdriver
from  selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

from wordcloud import WordCloud
import konlpy
from matplotlib import pyplot as plt
from matplotlib import font_manager as fm


from gensim.models import Word2Vec
import networkx as nx
from matplotlib import rc
from konlpy.tag import Okt
import re
import pickle
import csv
import numpy as np

from gensim.models.ldamodel import LdaModel
from gensim.models.callbacks import CoherenceMetric
from gensim import corpora
from gensim.models.callbacks import PerplexityMetric

import pyLDAvis.gensim_models as gensimvis
import pyLDAvis
from gensim.models.coherencemodel import CoherenceModel
import matplotlib.pyplot as plt

import instaloader


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
    """
    def installff():
        os.system('sbase install geckodriver')
        os.system('ln -s /home/appuser/venv/lib/python3.7/site-packages/seleniumbase/drivers/geckodriver /home/appuser/venv/bin/geckodriver')

    _ = installff()
    service = Service(GeckoDriverManager().install())
    """
    options = Options() 
    options.add_argument("--headless=new")
    #options.binary_location = 'C:/Program Files/Mozilla Firefox/firefox.exe'
    driver = webdriver.Chrome(options=options)
    #driver = webdriver.Firefox(options=options, service=service)
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
    col = ['작성자','시간','comment']

    df = pd.DataFrame(list_sum, columns=col)
    return df
    #df.to_csv(directory+'/'+path+'/'+'naver_'+str(num)+'.csv')

def get_nouns(tokenizer, sentence):
    tagged = tokenizer.pos(sentence)
    nouns = [s for s, t in tagged if t in ['NNG', 'NNP', 'VA', 'XR','Noun'] and len(s) >1]
    return nouns

def clean_text(text):
    text = text.replace(".", "").strip()
    text = text.replace("·", " ").strip()
    pattern = '[^ ㄱ-ㅣ가-힣|0-9]+'
    text = re.sub(pattern=pattern, repl='', string=text)
    return text

def save_processed_data(processed_data, title):
    with open("tokenized_data_"+title, 'w', newline="", encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        for data in processed_data:
            writer.writerow(data)
            
            
def instaCrawler(post_url):

    post_shortcode = post_url.split('/')[-2]
    post = instaloader.Post.from_shortcode(L.context, post_shortcode)
    
    usr_id = str(post.owner_profile).split(" ")[1]
    num_likes = post.likes
    
    
    # 댓글을 추출합니다.
    comments = []
    for commentt in post.get_comments():
        comments.append({
            'id': commentt.id,
            'comment': commentt.text,
            'created_at': commentt.created_at_utc,
            'owner': commentt.owner.username
        })
    likes = [num_likes]*len(comments)
    df = pd.DataFrame(comments)
    df["likes"] = likes 
    return usr_id, df       


@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8-sig')


@st.cache_data
def to_excel(dfs, ids):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    for d in range(len(dfs)):
        df1 = dfs[d]
        id1 = ids[d]
        df1.to_excel(writer, index=False, sheet_name=id1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data





tab1, tab2, tab3, tab4, tab5 = st.tabs(["You tube", "Naver", "URL All", "Insta", "NLP"])

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
            "[Download] Press Download Youtube Reply",
            csv,
            videoid + ".csv",
            key="download_csv")


with tab2:
    url_naver = st.text_input("Naver Reply Link")
    num       = st.text_input("Comment")
    
    if st.button("Crawl Naver News Reply"):
        with st.spinner('Wait for it...'):
            df = getNavernewsReply(url_naver, num, "naver", wait_time=3, delay_time=0.2)
        st.success('Done!')
        csv = convert_df(df)
        st.download_button(
            "[Download] Press Download Naver Reply",
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
                        label = "[Download] Download zip",
                        data = buf.getvalue(),
                        file_name = "mydownload.zip"
                        )
        st.balloons()
                
with tab4:
    uploaded_files_instalink =  st.file_uploader("Upload your insta Links",type=['csv'],accept_multiple_files=False)
    idd = st.text_input("Instagram ID")
    pww = st.text_input("Instagram PW", type="password")
    if st.button("Crawling"):
        urls = list(pd.read_csv(uploaded_files_instalink)["url"])
        L = instaloader.Instaloader()
        try:
            L.login(idd, pww)
            st.write("Success Login")
        except Exception as e:
            st.write("인스타그램에 로그인하여 본인 확인을 진행하세요.")
            st.error(f"An error occurred: {e}")
            
        
        ids = []
        dfs =[]
    
        my_bar3 = st.progress(0.0, text="Now Crawling Reply")
        for u in range(len(urls)):
            my_bar3.progress(100*(u+1)//len(urls))
            usr_id, df = instaCrawler(urls[u])
            ids.append(usr_id)
            dfs.append(df)
        # CSV 파일로 저장
        excel_data = to_excel(dfs, ids)
        
        st.download_button(
                label = "Download Excel",
                data  = excel_data,
                file_name = 'InstaReply.xlsx',
                mime = "application/vnd.ms-excel"
            )
                        
                    


with tab5:
    uploaded_files_csv =  st.file_uploader("Upload your reply csv",type=['csv','xlsx'],accept_multiple_files=True)
    sel_data = st.text_input("[Network Analysis] Select Top N")
    sel_data2 = st.text_input("[Topic Modeling] Select Cluster N")
    sel_data3 = st.text_input("[Topic Modeling] Topic File Name")
    progress_text = "Now Load Reply"
    my_bar2 = st.progress(0.0, text=progress_text)
    #plt.rcParams["font.family"] = os.path.join(os.getcwd(), "Gothic_A1/GothicA1-Light.ttf")
    #fpath = os.path.join(os.getcwd(), "Gothic_A1/GothicA1-Light.ttf")
    #prop = fm.FontProperties(fname=fpath)
    
    
    path_all = uploaded_files_csv
    df = pd.DataFrame()
    each_len = []
    for idx in range(len(path_all)):
        #st.write(path_all[idx].name)
        my_bar2.progress(100*(idx+1)//len(path_all))
        if str(path_all[idx].name).endswith("csv"):
            df_unit = pd.read_csv(path_all[idx])
            df_unit = df_unit["comment"]
            each_len.append(len(df_unit))
        elif str(path_all[idx].name).endswith("xlsx"):
            df_unit = pd.read_excel(path_all[idx], sheet_name=None)
            df_unit = pd.concat(df_unit, ignore_index=True)
            df_unit = df_unit["comment"]
            each_len.append(len(df_unit))
            
        df = pd.concat([df, df_unit], ignore_index = True)
        
    if st.button("Summarizing All Reply"):
        
        st.table(df.head(5))
        st.write("All Data Length : "+str(len(df)))
        st.write(each_len)
        
        csv11 = convert_df(df)
        st.download_button(
            "[Download] Press Data Download",
            csv11,
            "reply.csv",
            key="download_csv")
        
    if st.button("WordCloud"):
        with st.spinner("Now Make Wordcloud"):
                
            kkma = konlpy.tag.Kkma() 
            df.columns = ["comment"]
            text = df["comment"].str.replace('[^가-힣]', ' ', regex = True)
            
            nouns = text.apply(kkma.nouns)
            
            nouns = nouns.explode()
            
            df_word = pd.DataFrame({'word' : nouns})
            df_word['count'] = df_word['word'].str.len()
            df_word = df_word.query('count >= 2')
            
            df_word = df_word.groupby('word', as_index = False).count().sort_values('count', ascending = False)
            
            dic_word = df_word.set_index('word').to_dict()['count']
            
            wc = WordCloud(random_state = 123, font_path = '/usr/share/fonts/nanum/NanumGothic.ttf', width = 400,
                           height = 400, max_font_size = 150, background_color = 'white',colormap='inferno')
            
            img_wordcloud = wc.generate_from_frequencies(dic_word)
            
            fig = plt.figure(figsize = (15, 15)) # 크기 지정하기
            plt.axis('off') # 축 없애기
            plt.imshow(img_wordcloud) # 결과 보여주기
            plt.show()
            st.pyplot(fig)
            
            csv1 = convert_df(df_word)
            st.download_button(
                "[Download] Press Wordcloud Download",
                csv1,
                "wordcloud.csv",
                key="download_csv")

    if st.button("Network Analysis",help='Select Top N'):
        
        with st.spinner("Now Make Word Relations"):

            font_name = fm.FontProperties(fname='/usr/share/fonts/nanum/NanumGothic.ttf').get_name()
            rc('font', family=font_name)
       
            kkma = konlpy.tag.Kkma() 
            #df = pd.DataFrame(df, columns = ["comment"])
            df.columns = ["comment"]
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
            
            csv2 = convert_df(df)
            st.download_button(
                "[Download] Press Network Download",
                csv2,
                "wordnetwork.csv",
                key="download_csv")
            
            G=nx.Graph()
            
            
            sel = int(sel_data) # len(df)
            
            for i in range(sel):
                df_unit = df.iloc[i]
                node1, node2 = df_unit['source'], df_unit['target']
                weight = df_unit["weight"]
                G.add_edge(node1,node2,weight=weight)
            
   
            #plt.rcParams["font.family"] = os.path.join(os.getcwd(), "Gothic_A1/GothicA1-Light.ttf")
            pos = nx.spring_layout(G, k=0.2)
            fig1 = plt.figure(figsize=(12,8))
            nx.draw_networkx(G, pos,
                             node_size = 10,
                             node_color = "green",
                             alpha=.8,
                             font_size=18,
                             #fontproperties=font_prop
                             font_family = font_name,
                             #font_family='NanumMyeongjo'
                             )
            plt.show()
            st.pyplot(fig1)
    
    if st.button("Topic"):
        
        with st.spinner("Now Make DataFrame"):
            
            title = "reply.csv"
            df.columns = ["comment"]
            df.dropna(how='any')
            
            tokenizer = Okt()
            processed_data = []
            for sent in df['comment']:
                sentence = clean_text(str(sent).replace("\n", "").strip())
                processed_data.append(get_nouns(tokenizer, sentence))
            
            
            save_processed_data(processed_data,title)
            
            processed_data = [sent.strip().split(",") for sent in open("tokenized_data_"+title,'r',encoding='utf-8-sig').readlines()]
            processed_data = pd.DataFrame(processed_data)
            processed_data[0] = processed_data[0].replace("", np.nan)
            processed_data = processed_data[processed_data[0].notnull()]
            processed_data = processed_data.values.tolist()
            processed_data2=[]
            for i in processed_data:
                i=list(filter(None, i))
                processed_data2.append(i)
            processed_data = processed_data2
            
        
            with st.spinner("Now Make Topic Modeling"):
                 
                dictionary = corpora.Dictionary(processed_data)
                dictionary.filter_extremes(no_below=2, no_above=0.5)
                corpus = [dictionary.doc2bow(text) for text in processed_data]
                
                num_topics = int(sel_data2)
                chunksize = 2000
                passes = 20
                iterations = 400
                eval_every = None
                
                temp = dictionary[0]
                id2word = dictionary.id2token
                
                model = LdaModel(
                    corpus=corpus,
                    id2word=id2word,
                    chunksize=chunksize,
                    alpha='auto',
                    eta='auto',
                    iterations=iterations,
                    num_topics=num_topics,
                    passes=passes,
                    eval_every=eval_every
                )
                
                top_topics = model.top_topics(corpus) #, num_words=20)
                
                df_corpus = pd.DataFrame()
                for cc in range(len(top_topics)):

                    df_unit = pd.DataFrame(top_topics[cc][0])
                    df_corpus = pd.concat([df_corpus, df_unit], ignore_index = True, axis=1)
                    
                
                # Average topic coherence is the sum of topic coherences of all topics, divided by the number of topics.
                avg_topic_coherence = sum([t[1] for t in top_topics]) / num_topics
                print('Average topic coherence: %.4f.' % avg_topic_coherence)
                
                lda_visualization = gensimvis.prepare(model, corpus, dictionary, sort_topics=False)
                pyLDAvis.save_html(lda_visualization, str(sel_data3) + '_file_name.html')
                
                
                df_corpus.to_csv("corpusTop20.csv",index=False, encoding="utf-8-sig")
                    
                csv3 = convert_df(df_corpus)
                st.download_button(
                    "[Download] Press Topic Word Download",
                    csv3,
                    "corpusTop20.csv",
                    key="download_csv")
                
                    
                with open(str(sel_data3) + '_file_name.html', "r", encoding='utf-8-sig') as f:
                    st.download_button(
                        "[Download] Press Topic Word HTML Download",
                        data=f,
                        file_name=str(sel_data3) + '_file_name.html',
                        )

                #st.write("Save Directory : " + os.getcwd())
                st.write("HTML File Name : " +'file_name.html')
                st.write("CSV  File Name : " +"corpusTop20.csv")