############################################################################################
# IMPORTS
############################################################################################
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

#import tensorflow.keras.backend as K
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import ConfusionMatrixDisplay


import warnings
warnings.filterwarnings('ignore')

import tensorflow as tf
#import tensorflow.keras as keras

from tensorflow.keras import layers
from tensorflow.keras import regularizers


from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Dense, MaxPooling2D, Activation, Flatten

from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical



from IPython import display
from PIL import Image


import pathlib
import shutil
import tempfile
import concurrent

import pickle
import visualkeras

import json
import glob
import PIL

#import panel as pn
import streamlit as st
from streamlit_image_zoom import image_zoom
import joblib
from copy import deepcopy

st.set_page_config(page_title="Umami Analyzer", layout="wide")

print(tf.config.list_physical_devices())
print('Streamlit ver.: ' + st.__version__)
print('SciKit-learn ver.: ' + sklearn.__version__)
print('TensorFlow ver.: ' + tf.__version__)
print('Joblib ver.: ' + joblib.__version__)



gpu_dev = tf.config.experimental.list_physical_devices('GPU')
for itm in gpu_dev:
    tf.config.experimental.set_memory_growth(itm, True)
############################################################################################
# CONSTANTS
############################################################################################
TREE_MODEL = './models/random_forest_model.pkl'
LAYER_2 = './models/Nadine_food-101-EfNetB3-A0.__-earlystop-E__of45-B32_softCat_v1.1b.keras'
LAYER_2_SIZE = (300,300)
SEED = 111
TABLE = './data/food-101/Final_table_dish_info.csv'
LOGO = './images/Umami_logo_vertical.png'

TEXT_SIZE_1 = '20px'
TEXT_SIZE_1_1 = '40px'
TEXT_SIZE_2 = '14px'
TEXT_SIZE_BLOCK = '20px'
TEXT_SIZE_ICONS = '20px'

CACHED = True


############################################################################################
# FUNCTIONS - https://www.analyticsvidhya.com/blog/2023/12/grad-cam-in-deep-learning/
############################################################################################

def make_gradcam_heatmap(img_array, model, last_conv_layer_name):
   
    grad_model = tf.keras.models.Model(
        [model.inputs],
        [model.get_layer(last_conv_layer_name).output, model.output]
    )
    with tf.GradientTape() as tape:
       # conv_outputs, predictions = grad_model(img_array)
        outputs = grad_model(img_array)
        conv_outputs = outputs[0]
        
        
        if isinstance(outputs[1], list):
            predictions = tf.convert_to_tensor(outputs[1][0])
        else:
            predictions = tf.convert_to_tensor(outputs[1])
        
        
        raw_index = tf.argmax(predictions, axis=1)
        pred_index = int(np.ravel(raw_index.numpy())[0])
        class_channel = predictions[:, pred_index]
    
    grads = tape.gradient(class_channel, conv_outputs)
    
    if grads is None:
        raise ValueError(f"Layer {last_conv_layer_name} is not suitable for Grad-CAM (no gradients found).")
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()


def display_gradcam(img, heatmap, alpha=0.8, cmap="jet"):
   
    import matplotlib.cm as cm

    ## Rescale heatmap to a range 0-255
    heatmap = np.uint8(255 * heatmap)

    ## Use jet colormap to colorize heatmap
    colormap = cm.get_cmap(cmap)


    heatmap = colormap(heatmap)[:, :, :3]
    heatmap = Image.fromarray((heatmap * 255).astype("uint8")).resize(img.size)
    heatmap = np.array(heatmap)

    ## Superimpose the heatmap on original image
    superimposed_img = np.array(img) * (1 - alpha) + heatmap * alpha
    
    return np.uint8(superimposed_img)

def goto(linenum):
    global line
    line = linenum


@st.cache_resource
def load_layer_1_base():
    model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    return model
@st.cache_resource
def load_layer_1_tree(path):
    return joblib.load(path)
@st.cache_resource
def load_layer_2(path):
    model = tf.keras.models.load_model(path)
    for layer in model.layers:
        layer.trainable = False
    return model


############################################################################################
# DATA TABLE LOAD - ALL WE KNOW ABOUT FOOD CLASSES IS HERE
############################################################################################
data_df = pd.read_csv(TABLE)
data_df.columns = [val.lower().strip().replace(' ','_') for val in data_df.columns.tolist()]

############################################################################################
# STREAMLIT - THE BEGINNING
############################################################################################
st.markdown(f'''
    <style>
        section[data-testid="stSidebar"] .css-ng1t4o {{width: 14rem;}}
        section[data-testid="stSidebar"] .css-1d391kg {{width: 14rem;}}
    </style>
''',unsafe_allow_html=True)

st.sidebar.image(LOGO, width=180)




camera_on = False

left_col, right_col = st.columns(2)
source = st.sidebar.radio("Select source of an image", ("Built-in examples","Load from computer","Camera"),index=0)
match source:
    case "Built-in examples":
        option = st.sidebar.selectbox('Try out built-in examples...',('Example 1 - sushi',
                                            'Example 2 - sandwich',
                                            'Example 3 - DeutscheBahn',
                                            'Example 4 - pizza',
                                            'Example 5 - apple pie'), index=0)
        match option:
            case 'Example 1 - sushi': image_path='./data/sushi.jpg'
            case 'Example 2 - sandwich': image_path='./data/sandwich.jpg'
            case 'Example 3 - DeutscheBahn': image_path='./data/railroad_train.jpg'
            case 'Example 4 - pizza': image_path='./data/pizza.jpg'
            case 'Example 5 - apple pie': image_path='./data/apple_pie.jpg'
        with left_col:
            st.image(tf.keras.utils.load_img(image_path), use_container_width=True)
    case "Load from computer":
        st.session_state.uploaded = st.sidebar.file_uploader(
            "Choose your own image file:",
            accept_multiple_files=False,
            type=["png", "jpg", "jpeg", "tiff", "bmp"],
            key="file_uploader1")
        if st.session_state.uploaded is not None:
            image_path = st.session_state.uploaded
        else:
            image_path = './data/sushi.jpg'
        with left_col:
             st.image(tf.keras.utils.load_img(image_path), use_container_width=True)
        

    case "Camera":
        with left_col:
            camera_on = True
            picture = st.camera_input("Take a picture", disabled=False)
            if picture is not None:
                bytes_data = picture.getvalue()
                img_tensor = tf.io.decode_image(bytes_data, channels=3, dtype=tf.uint8)


force_heatmap = st.sidebar.checkbox('Force GradCAM output.', value=False, key=None, help=None, on_change=None, label_visibility="visible")


############################################################################################
#  MODELS SELECTION MENU (uncomment to try - model 2 error)
############################################################################################
option_2 = st.sidebar.selectbox('Try out different models:',('L2 - EfNetB3_v1a', 'L2 - EfNetB0_v1'), index=0)
match option_2:
    case 'L2 - EfNetB3_v1a':
        LAYER_2 = './models/Nadine_food-101-EfNetB3-A0.__-earlystop-E__of45-B32_softCat_v1.1b.keras'
        LAYER_2_SIZE = (300,300)
    case 'L2 - EfNetB0_v1': 
        LAYER_2 = './models/6_7_final_classification101_EfficientNet.keras'
        LAYER_2_SIZE = (224,224)  
    
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Technical Overview"):
    st.markdown(f"""
    <div style="font-size: {TEXT_SIZE_2};">
    <b>Umami Analyzer</b> is a food recognition system.
    <br><br>
    <b>Architecture:</b>
    <ul>
        <li><b>Stage 1:</b> Random Forest (ResNet50) for food/non-food filtering.</li>
        <li><b>Stage 2:</b> Fine-tuned <b>EfficientNetB3</b> for 101-class classification.</li>
        <li><b>Visuals:</b> <b>Grad-CAM</b> for model interpretability.</li>
    </ul>
    <i>Developed as a portfolio project.</i>
    </div>
    """, unsafe_allow_html=True)
        


############################################################################################
#  MODELS LOAD
############################################################################################

if CACHED:
    layer_1_base = load_layer_1_base()
    layer_1_tree = load_layer_1_tree(TREE_MODEL)
    layer_2 = load_layer_2(LAYER_2)

else:
    layer_1_base = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    layer_1_tree = joblib.load(TREE_MODEL)
    layer_2 = tf.keras.models.load_model(LAYER_2)
    for layer in layer_2.layers:
        layer.trainable = False

############################################################################################
# 5.1 IMAGE LOAD
############################################################################################


if camera_on and (picture is not None):
    tf.keras.utils.save_img('./data/CAMERA.jpg', img_tensor, data_format=None, file_format=None, scale=True)
    img_full = tf.keras.utils.load_img('./data/CAMERA.jpg')
    img_l1 = tf.keras.utils.load_img('./data/CAMERA.jpg', target_size=(224, 224))
    img_l2 = tf.keras.utils.load_img('./data/CAMERA.jpg', target_size=LAYER_2_SIZE)
    if os.path.isfile('./data/CAMERA.jpg'):
        os.remove('./data/CAMERA.jpg')
    img_array_l1 = tf.keras.utils.img_to_array(img_l1)
    img_array_l2 = tf.keras.utils.img_to_array(img_l2)




elif not camera_on:
    img_full = tf.keras.utils.load_img(image_path)

    img_l1 = tf.keras.utils.load_img(image_path, target_size=(224, 224))
    img_l2 = tf.keras.utils.load_img(image_path, target_size=LAYER_2_SIZE)
        
    img_array_l1 = tf.keras.utils.img_to_array(img_l1)
    img_array_l2 = tf.keras.utils.img_to_array(img_l2)
else:
    st.write("Waiting for the photo...")




if (not camera_on) or (picture is not None):
    if st.button("What is it???", type="primary"):
        ############################################################################################
        # LAYER 1 PREDICT - IS IT A FOOD AT ALL?
        ############################################################################################
        features = layer_1_base.predict(tf.keras.applications.resnet50.preprocess_input(np.expand_dims(img_array_l1, axis=0)))
        prediction = layer_1_tree.predict(features.reshape(1, -1))

        l1_prob = prediction
        l1_label = "Food" if prediction[0] == 0 else "Non-Food"
        probable_labels = []
        probable_cert = []

        if (l1_label=='Food'):
            st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">Well, it\'s a <b style="color:#50b432; font-size: {TEXT_SIZE_1};">Food</b></p>', unsafe_allow_html=True)
            ############################################################################################
            # IF FOOD - LAYER 2 PREDICTION
            ############################################################################################
            pred_l2 = layer_2.predict(tf.keras.preprocessing.image.smart_resize(tf.expand_dims(img_array_l2, axis=0), size=LAYER_2_SIZE))
            l2_label = str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'dish_name'])
            l2_prob = pred_l2.max() * 100
            l2_label = str(l2_label).replace("['","").replace("']","").replace("_"," ").upper()
            flags = data_df.at[int(np.argmax(pred_l2, axis = -1)), 'flags']
            certainty = str(l2_prob.round(2)) + '%'
            if (l2_prob.round(2) >=90):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1_1};">I can bet it is <b style="color:#28a745; font-size: {TEXT_SIZE_1_1};">{l2_label}</b>!&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) < 90) and (l2_prob.round(2) >= 75):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1_1};">I pretty much sure it is <b style="color:#8cc63f; font-size: {TEXT_SIZE_1_1};">{l2_label}</b>!&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) <75) and (l2_prob.round(2) >=55):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1_1};">I tend to believe it is <b style="color:#ffc107; font-size: {TEXT_SIZE_1_1};">{l2_label}</b>.&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) <55) and (l2_prob.round(2) >=35):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1_1};">I\'d guess it is <b style="color:#fd7e14; font-size: {TEXT_SIZE_1_1};">{l2_label}</b>.&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) <35) and (l2_prob.round(2) >=15):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1_1};">Oh, this one is tough! Perhaps, <b style="color:#e44d26; font-size: {TEXT_SIZE_1_1};">{l2_label}</b>?&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1_1};">If I had to guess, I\'d say it is <b style="color:Red; font-size: {TEXT_SIZE_1_1};">{l2_label}</b>...&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            st.markdown("___")
            
          

    ############################################################################################
            # 4. IMAGE and GRADCAM HEATMAP SHOW
    ############################################################################################
         
            last_conv_layer_name=layer_2.layers[-5].name

            heatmap = make_gradcam_heatmap(
                    img_array=tf.expand_dims(img_array_l2, axis=0), 
                    model=layer_2, 
                    last_conv_layer_name=last_conv_layer_name
                )

            heated_image = display_gradcam(img=img_full, heatmap=heatmap, alpha=0.6)
            with right_col:
               st.image(heated_image, use_container_width=True)
            left_cat_col, right_cat_col = st.columns(2)
                


    ############################################################################################
            # COMBINED SECTION: ALLERGENS & DIETARY STATUS
     ############################################################################################
         
            status_row_l, status_row_r = st.columns([3, 1])

            with status_row_l:
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_BLOCK}; margin-bottom: 10px;"><b>Allergens:</b></p>', unsafe_allow_html=True)
                
             
                allergens = str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'all_allergens']).split(",")
                allergens = [val.strip() for val in allergens if val.strip()]
              
                if allergens:
                    
                    num_al = len(allergens)
                    al_cols = st.columns(max(num_al, 6)) 
                    for itr in range(num_al):
                        with al_cols[itr]:
                            st.image('./images/icons/' + str(allergens[itr]) + '.svg', width=45, caption=allergens[itr])
                else:
                    st.write("No allergens detected.")

            with status_row_r:
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_BLOCK}; margin-bottom: 10px;"><b>Dietary:</b></p>', unsafe_allow_html=True)
                status = str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'dietary_status'])
                
                # Цвет текста в зависимости от статуса
                status_color = "#50b432" if "Vegetarian" in status else "Red"
                
                # Выводим иконку и текст рядом
                st.markdown(f'<p style="color:{status_color}; font-size: {TEXT_SIZE_ICONS}; margin-bottom: 5px;"><b>{status}<b></p>', unsafe_allow_html=True)
                try:
                    st.image('./images/icons/' + str(status) + '.svg', width=50)
                except:
                    pass 
            st.markdown("___")        
            
            ############################################################################################
    #         # SHOW TABS - Components, Pie chart
    #       ############################################################################################
    #     
            ing_col, nutr_col = st.columns([2, 1]) 

            with ing_col:
                st.markdown(f'### 🍳 Recipe & Ingredients')
                
                raw_main_ing = str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'classic_recipe'])
                
                if "Time:" in raw_main_ing:
                    time_part = raw_main_ing.split("Time:")[1].split(";")[0].strip()
                    st.success(f"⏱️ **Estimated Cooking Time:** {time_part}")
                   
                    clean_ingredients = raw_main_ing.split("Time:")[0].strip()
                else:
                    clean_ingredients = raw_main_ing

            
                formatted_rows = clean_ingredients.replace(';', '\n\n').strip()

              
                st.markdown(f'<p style="color:#50b432; font-size: {TEXT_SIZE_1}; margin-bottom: 5px;"><b>Main ingredients:</b></p>', unsafe_allow_html=True)
                
            
                with st.container(border=True):
                    st.markdown(formatted_rows)

                optional_ing = data_df.at[int(np.argmax(pred_l2, axis = -1)), 'optional_ingredients']
                if str(optional_ing).lower() != 'nan' and optional_ing != "":
                    st.markdown(f'<p style="color:#058dc7; font-size: {TEXT_SIZE_1}; margin-top: 15px;"><b>✨ Optional Extras:</b></p>', unsafe_allow_html=True)
                    st.caption(optional_ing)
            
            with nutr_col:
               
                nutrients_text = data_df.at[int(np.argmax(pred_l2, axis = -1)), 'nutrients_per_100g']
                st.markdown(f'<h5 style="text-align: center; margin-bottom: -20px;">{nutrients_text} per 100g</h5>', unsafe_allow_html=True)
                
               
                nutr_df = data_df[['proteins','fats','carbs']].iloc[int(np.argmax(pred_l2, axis = -1))].apply(lambda x: x.split("g")[0])
                pie_data = [int(nutr_df.proteins), int(nutr_df.fats), int(nutr_df.carbs)]
                labels = ['Proteins', 'Fats', 'Carbs']
                colours = ['#00b67b', '#ffd962', '#7ca5f9']
                
               
                fig, ax = plt.subplots(figsize=(6, 4)) 
                
        
                ax.pie(
                    pie_data, 
                    labels=labels, 
                    autopct='%1.0f%%', 
                    startangle=90, 
                    colors=colours,
                    radius=0.8,      
                    textprops={'fontsize': 14}
                )
                
               
                ax.axis('equal') 
                plt.tight_layout()
                
             
                st.pyplot(fig, use_container_width=True)

        

###############3##########
#TOP 2-5
            all_probs = pred_l2[0].copy()
            top5_indices = np.argsort(all_probs)[-5:][::-1]
            
            probable_labels = []
            probable_cert = []
            
            for idx in top5_indices:
                name = str(data_df.at[idx, 'dish_name']).replace("_", " ").upper()
                prob = all_probs[idx] * 100
                probable_labels.append(name)
                probable_cert.append(prob)

            if round(l2_prob, 2) < 94.99:
                st.markdown("---")
                st.markdown("#### 📊 Probability Analysis (Alternatives)")
                
                chart_df = pd.DataFrame({
                    'Dish': probable_labels[1:], 
                    'Confidence': probable_cert[1:]
                }).sort_values('Confidence', ascending=True)

                import plotly.express as px
                fig = px.bar(
                    chart_df, x='Confidence', y='Dish', orientation='h',
                    text='Confidence', color_discrete_sequence=['#5D6D7E']
                )

                fig.update_layout(
                    width=550, height=220,
                    margin=dict(l=10, r=120, t=5, b=60), 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis_title=None,
                    showlegend=False
                )

                fig.update_xaxes(
                    range=[0, 100],            
                    tickvals=[0, 50, 100],     
                    ticktext=['0%', '50%', '100%'],
                    showgrid=False,            
                    zeroline=True,
                    zerolinecolor='#D3D3D3',   
                    title_text="<i>*Compared to the ideal 100% match*</i>", 
                    title_font=dict(size=12, color='black')
                )

                
                fig.add_vline(x=50, line_width=0.5, line_color="#D3D3D3")
                fig.add_vline(x=100, line_width=0.5, line_color="#D3D3D3")

                fig.update_yaxes(tickfont=dict(size=13, color='black'))

                fig.update_traces(
                    texttemplate='<b>%{text:.2f}%</b>', 
                    textposition='outside',
                    textfont=dict(size=14, color='black'),
                    width=0.4, 
                    cliponaxis=False 
                )
                
                st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})


            ############################################################################################
            # OTHER TOP 4 PROBABILITIES
            ############################################################################################
            st.markdown("___")
            with st.expander("**It may also be...**"):
                for itr in range(5):
                    probable_labels.append( str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'dish_name']).replace("['","").replace("']","").replace("_"," ").upper() )
                    probable_cert.append(pred_l2.max()*100)
                    pred_l2 = np.delete(pred_l2, np.argmax(pred_l2))
                    if itr >0:
                        #st.write(f"{itr}. {probable_labels[itr].upper()}, certainty: {probable_cert[itr].round(2)}%")
                        st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">{probable_labels[itr].upper()}, certainty: <b style="color:Red; font-size: {TEXT_SIZE_1};">{probable_cert[itr].round(2)}%</b></p>', unsafe_allow_html=True)

            
            
            
            

        ############################################################################################
        # IF FORCE FLAG TRIGGERED, BUT IT'S NOT A FOOD
        ############################################################################################
        elif (force_heatmap) and (l1_label=='Non-Food'):
            st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">Since you insist...</p>', unsafe_allow_html=True)
            ############################################################################################
            # 5.3 LAYER 2 PREDICT
            ############################################################################################
            pred_l2 = layer_2.predict(tf.keras.preprocessing.image.smart_resize(tf.expand_dims(img_array_l2, axis=0), size=LAYER_2_SIZE))
            l2_label = str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'dish_name'])
            l2_prob = pred_l2.max()
            l2_label = str(l2_label).replace("['","").replace("']","").replace("_"," ").upper()
            flags = data_df.at[int(np.argmax(pred_l2, axis = -1)), 'flags']
            certainty = str(l2_prob.round(2)) + '%'
            if (l2_prob.round(2) >=90):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">I can bet it is <b style="color:Red; font-size: {TEXT_SIZE_1};">{l2_label}</b>!&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) < 90) and (l2_prob.round(2) >= 75):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">I pretty much sure it is <b style="color:Red; font-size: {TEXT_SIZE_1};">{l2_label}</b>!&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) <75) and (l2_prob.round(2) >=55):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">I tend to believe it is <b style="color:Red; font-size: {TEXT_SIZE_1};">{l2_label}</b>.&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) <55) and (l2_prob.round(2) >=35):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">I\'d guess it is <b style="color:Red; font-size: {TEXT_SIZE_1};">{l2_label}</b>.&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            elif (l2_prob.round(2) <35) and (l2_prob.round(2) >=15):
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">Oh, this one is tough! Perhaps, <b style="color:Red; font-size: {TEXT_SIZE_1};">{l2_label}</b>?&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:Black; font-size: {TEXT_SIZE_1};">If I had to guess, I\'d say it is <b style="color:Red; font-size: {TEXT_SIZE_1};">{l2_label}</b>...&ensp;{flags}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#b0b0b0; font-size: {TEXT_SIZE_2};">Certainty: {certainty}</p>', unsafe_allow_html=True)
            ############################################################################################
            # 4. IMAGE and GRADCAM HEATMAP SHOW
            ############################################################################################
            last_conv_layer_name=layer_2.layers[-5].name

            heatmap = make_gradcam_heatmap(
                    img_array=tf.expand_dims(img_array_l2, axis=0), 
                    model=layer_2, 
                    last_conv_layer_name=last_conv_layer_name
                )

            heated_image = display_gradcam(img=img_full, heatmap=heatmap, alpha=0.6)
            with right_col:
               st.image(heated_image, use_container_width=True)
            left_cat_col, right_cat_col = st.columns(2)
            


            ############################################################################################
            # OTHER TOP 4 PROBABILITIES - NON-FOOD!!!
            ############################################################################################
            with st.expander("Other most probable classes:"):
                for itr in range(5):
                    probable_labels.append( str(data_df.at[int(np.argmax(pred_l2, axis = -1)), 'dish_name']).replace("['","").replace("']","").replace("_"," ").upper() )
                    probable_cert.append(pred_l2.max()*100)
                    pred_l2 = np.delete(pred_l2, np.argmax(pred_l2))
                    if itr >0:
                        st.write(f"{itr}. {probable_labels[itr].upper()}, probability {probable_cert[itr].round(2)}")


        else:
                st.write('No food was found on the image.')
    
