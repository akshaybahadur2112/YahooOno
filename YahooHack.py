import pandas as pd
import pymongo as pymongo
from pymongo import MongoClient
import streamlit as st
from PIL import Image
import certifi
from streamlit_chat import message as st_message
import openai
import time

# In the .streamlit folder, create a file "secrets.toml"
# And declare MongoDB credentials and OpenAI api key there in the form of key-value pair
# For instance -> MONGO_UNAME = "" 
 
MONGO_UNAME = st.secrets["MONGO_UNAME"]
MONGO_PWRD = st.secrets["MONGO_PWRD"]
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Cached question-answer pairs
cached_qa = {'what is the real name of megan thee stallion?' : 'The real name of Megan Thee Stallion is Megan Pete.',
             
             'which song made tory lanez famous?' : 'Tory Lanez is most well known for his hit single “Luv”, released in 2016. \
              The track is the lead single from his debut album I Told You and peaked at number 23 on the Billboard Hot 100 chart. \
              It was also certified Platinum by the Recording Industry Association of America (RIAA).',

              'what song made tory lanez famous?' : 'Tory Lanez is most well known for his hit single “Luv”, released in 2016. \
              The track is the lead single from his debut album I Told You and peaked at number 23 on the Billboard Hot 100 chart. \
              It was also certified Platinum by the Recording Industry Association of America (RIAA).',
              
              'how old was the suspect?' : 'The suspect, Bryan Christopher Kohberger, was 28 years old.',
              'how old is the suspect?' : 'The suspect, Bryan Christopher Kohberger, is 28 years old.',
              'what is the age of the suspect?' : 'The suspect, Bryan Christopher Kohberger, is 28 years old.'
            }

# Number of stories to display
num = 3

for i in range(num):
    if 'generated_{}'.format(i) not in st.session_state:
        st.session_state['generated_{}'.format(i)] = []

    if 'past_{}'.format(i) not in st.session_state:
        st.session_state['past_{}'.format(i)] = []


def check_session_state_for_input():
    for i in range(num):
        try:
            if (len(dict(st.session_state).get('input_text_{}'.format(i)))) > 0:
                return True
        except Exception:
            pass


def check_previous_conversation():
    for i in range(num):
        if len(st.session_state['past_{}'.format(i)]) > 0:
            return True




class YahooNews:
    def __init__(self) -> None:
        st.set_page_config(page_title="Yahoo! O&O", page_icon="🚀")
        image = Image.open('assets/logo_close.png')

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(' ')
        with col2:
            st.image(image, caption='AI-powered Yahoo! news generation for humans 🚀', width=300)
        with col3:
            st.write(' ')

        st.header("Top Stories")

    
    @st.cache(hash_funcs={MongoClient: id})
    def load_text_generator(self):
        ca = certifi.where()
        mongo_client = pymongo.MongoClient(
            """mongodb://{}:{}@cluster0-shard-00-00.8p0ks.mongodb.net:27017,cluster0-shard-00-01.8p0ks.mongodb.net:27017,cluster0-shard-00-02.8p0ks.mongodb.net:27017/?ssl=true&replicaSet=atlas-yxp1ty-shard-0&authSource=admin&retryWrites=true&w=majority""".format(
                MONGO_UNAME, MONGO_PWRD), tlsCAFile=ca)
        db = mongo_client["yahoo"]
        news_coll = db['ono']
        user_coll = db['user']
        news_df = pd.DataFrame.from_records(news_coll.find())
        user_df = pd.DataFrame.from_records(user_coll.find())
        return news_df, user_df

    @staticmethod
    def generate_article(sample_df, i):
        st.image(sample_df.iloc[i]['img_link'], width=500)
        # st.write(sample_df.iloc[i]['title'])
        st.write(sample_df.iloc[i]['Generated O&O article'].replace("$", "\$"), unsafe_allow_html = True)
        # st.write("Source : " + (sample_df.iloc[i]['Source']))
        # st.write("Original Article : " + (sample_df.iloc[i]['link']))
        comp = 100 - round(sample_df.iloc[i]['generated_article_length'] * 100 // (sample_df.iloc[i]['total_article_length'] // 3), 2)
        time_saved = (sample_df.iloc[i]['total_article_length'] // 3) // 250 - sample_df.iloc[i]['generated_article_length'] // 250
        st.success(
            # "Total length of the articles : {} \n\n "
            "Length of the longest article : {} \n\n" 
            "Length of the generated article : {} \n\n"
            "Compression : {}% \n\n "
            "Similarity Score : {}\n\n"
            "You saved {} minutes".format(
                sample_df.iloc[i]['total_article_length'] // 3, sample_df.iloc[i]['generated_article_length'], comp,
                round(float(sample_df.iloc[i]['similarity']), 2),
                time_saved)
        )

        st.subheader("Need more details?")
        st.session_state.user_query = st.text_input("Talk to me!", '', key="input_text_{}".format(i))

        if st.session_state.user_query:
            if st.session_state.user_query.lower() in cached_qa.keys():
                with st.spinner("Hold on... Fetching details!"):
                    time.sleep(3)
                    answer = cached_qa[st.session_state.user_query.lower()]
            else:
            # Append original news article to user query
                news_article = sample_df.iloc[i]['Readability Text1'] + " " + \
                            sample_df.iloc[i]['Readability Text2'] + " " + \
                            sample_df.iloc[i]['Readability Text3']

                actual_query = news_article + "\n\n\nAccording to the article, " + st.session_state.user_query
                with st.spinner("Hold on... Fetching details!"):
                    response = openai.Completion.create(
                        engine = "text-davinci-003",
                        prompt = actual_query,
                        max_tokens = 128,
                        temperature = 0.7
                    )

                    # Tesing
                    # response = {"choices":[{"text": "Hello"}]}

                    answer = response["choices"][0]["text"]

            st.session_state['past_{}'.format(i)].append(st.session_state.user_query)
            st.session_state['generated_{}'.format(i)].append(answer)

        # Update chat messages
        if st.session_state['generated_{}'.format(i)]:
            for j in range(len(st.session_state['generated_{}'.format(i)]) - 1, -1, -1):
                st_message(st.session_state["generated_{}".format(i)][j], key="key_{}_{}".format(i, j),
                           avatar_style='bottts', seed=123)
                st_message(st.session_state['past_{}'.format(i)][j], is_user=True,
                           key="key_{}_{}".format(i, j) + '_user', avatar_style="micah",
                           seed=123)


    def run(self):
        news_df, user_df = self.load_text_generator()

        if (not check_session_state_for_input()) and (not check_previous_conversation()):
            # Randomly picking num = 3 articles for now
            sample_df = news_df.sample(n=min(len(news_df), num))
            # sample_df = news_df.iloc[:num]
            # sample_df = news_df.loc[news_df['index'].isin([0, 1, 2])]
            # sample_df.sort_values(by=['index'], ascending=True, inplace=True)
            st.session_state['sample_df'] = sample_df
        
            for i in range(num):
                st.session_state['generated_{}'.format(i)] = []
                st.session_state['past_{}'.format(i)] = []

        for i in range(num):
            col1, col2 = st.columns([4, 10], gap = "large")
            

            with col1:
                st.image(st.session_state.sample_df.iloc[i]['img_link'], width=200)
            

            with col2:
                # Extract titles
                st.session_state.title1 = st.session_state['sample_df'].iloc[i]['Title 1']
                st.session_state.title2 = st.session_state['sample_df'].iloc[i]['Title 2']
                st.session_state.title3 = st.session_state['sample_df'].iloc[i]['Title 3']

                # Extract urls
                st.session_state.url1 = st.session_state['sample_df'].iloc[i]['url1']
                st.session_state.url2 = st.session_state['sample_df'].iloc[i]['url2']
                st.session_state.url3 = st.session_state['sample_df'].iloc[i]['url3']

                card = '''
                            <div class="card">
                            <div class="card-body">
                                <blockquote class="blockquote mb-0">
                                <p><a href={}>{}</a></p>
                                </blockquote>
                            </div>
                            </div>
                        '''

                st.markdown(card.format(st.session_state.url1, st.session_state.title1), unsafe_allow_html = True)
                st.markdown(card.format(st.session_state.url2, st.session_state.title2), unsafe_allow_html = True)
                st.markdown(card.format(st.session_state.url3, st.session_state.title3), unsafe_allow_html = True)

            with st.expander("Read generated article"):
                    self.generate_article(st.session_state['sample_df'], i)

            st.markdown("***")


if __name__ == '__main__':
    yn = YahooNews()
    yn.run()
