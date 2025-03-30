from scraper import get_data
import pandas as pd
import streamlit as st
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
from numpy import expm1


model = joblib.load('data/model.joblib')
df_original = pd.read_csv('data/data.csv')  # original dataset

def price_convert(value):
    if value >= 10000000:
        short_value = round(value / 10000000, 1)
        return f"{short_value} Crore" 

    elif value >= 100000:
        short_value = round(value / 100000, 1)
        return f"{short_value} Lakh"

def submit_fn(make,model_field,year,mileage,fuel_type,engine_capacity,transmission,city):
    # make,model,year,mileage,fuel_type,engine_capacity,transmission,city,price

    if make:
        make = make.strip()
    if model_field:
        model_field = model_field.strip()
    # if year:
    #     input_data['year'] = year
    # if not min_mileage:
    #     min_mileage = 0
    # if not max_mileage:
    #     max_mileage = 1000000
    # input_data['mileage'] = (min_mileage + max_mileage) / 2        
    # if fuel_type != 'Any':
    #     input_data['fuel_type'] = fuel_type
    # if engine_capacity:
    #     input_data['engine_capacity'] = engine_capacity
    # if trim:
    #     input_data['trim'] = trim
    # if transmission != 'Any':
    #     input_data['transmission'] = transmission
    if city:
        city = city.strip()
        # input_data['city'] = city

    if not make or not model_field or not year or not mileage or not city or not fuel_type or not transmission or not engine_capacity:
        st.error('Please fill in all the fields.')
        return
    
    input_data = {
        'make': make,
        'model': model_field,
        'year': year,
        'mileage': np.log1p(mileage),
        'fuel_type': fuel_type,
        'engine_capacity': engine_capacity,
        'transmission': transmission,
        'city': city,
        'age': 2025 - year,
        'mileage_per_year': np.log1p(mileage / ((2025-year)+1)),
        'engine_per_mileage': np.log1p(engine_capacity / (mileage+1))
    }

    df = pd.DataFrame([input_data])

    # # cleaning 'mileage' column
    # df['mileage'] = df['mileage'].astype(str).str.replace(r'[a-zA-Z,\s]+', '', regex=True)
    # df['mileage'] = pd.to_numeric(df['mileage'], errors='coerce')
    # df['mileage'] = df['mileage'].astype(int) # ensuring correct data type

    # # cleaning 'engine_capacity' column
    # if engine_capacity:
    #     df['engine_capacity'] = df['engine_capacity'].astype(str).str.replace(r'[a-zA-Z,\s]+', '', regex=True)
    #     df['engine_capacity'] = pd.to_numeric(df['engine_capacity'], errors='coerce')
    #     df['engine_capacity'] = df['engine_capacity'].astype(int) # ensuring correct data type

    # if year:
    #     df['year'] = df['year'].astype(int)


    
    # target encoding
    target_encoder = joblib.load('data/target_encoder.joblib')
    target_cols = ['make', 'model', 'city']
    df_encoded = target_encoder.transform(df[target_cols])
    df[target_cols] = df_encoded

    # categorical_cols = ["model", "make", "transmission", "fuel_type", "city"]
    # one hot encoding
    categorical_cols = ["transmission", "fuel_type"]
    encoder = joblib.load('data/onehot_encoder.joblib')
    encoded_features = encoder.transform(df[categorical_cols])
    encoded_df = pd.DataFrame(encoded_features, columns=encoder.get_feature_names_out(categorical_cols))
    df = pd.concat([df, encoded_df], axis=1).drop(columns=categorical_cols)

    # label encoding
    # encoders = joblib.load('data/label_encoders.joblib')
    # for col in categorical_cols:
    #     le = encoders[col]
    #     df[col] = le.transform(df[col].astype(str)) # important to cast to string to avoid errors.

    # scaling
    numerical_cols = ["year", "mileage", "engine_capacity", "age", "mileage_per_year", "engine_per_mileage"]
    # if year:
    #     numerical_cols.append("year")
    # if engine_capacity:
        # numerical_cols.append("engine_capacity")
    # df_original = pd.read_csv('data/data.csv')
    scaler = joblib.load('data/scaler.joblib')
    df[numerical_cols] = scaler.transform(df[numerical_cols].copy())
    
    df = df.reindex(columns=model.feature_names_in_, fill_value=0)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.width', None)
    print(df['make'].iloc[0])
    print(df['model'].iloc[0])
    print(df['year'].iloc[0])
    print(df['mileage'].iloc[0])
    print(df['city'].iloc[0])
    prediction = model.predict(df)

    if prediction and len(prediction) > 0:
        price = float(prediction[0])
        price = expm1(price)
        # print(price)
        new_price=price_convert(price)
        st.title(f'PKR {new_price}')
    else:
        st.title('An error occurred')

def update_model_fields():
    if st.session_state.make:
        condition = df_original['make'] == st.session_state.make
        model_list = df_original[condition]['model'].unique()
        st.session_state.model_list = model_list

if __name__ == '__main__':
    make_list=df_original['make'].unique()
    make_list=np.sort(make_list)
    if 'make' not in st.session_state: # run once initially only
        st.session_state.make = make_list[0]
        update_model_fields()    

    city_list=df_original['city'].unique()
    city_list=np.sort(city_list)


    
    st.set_page_config(page_title='Car Price Estimator', page_icon='🚘')
    st.title('🚘 Car Price Estimator (Pakistan)')
    st.info("Enter car details to get an accurate estimate of price. You can skip fields.")
    

    with st.container(border=False):
        st.header("Car Details")
        col1, col2 = st.columns(2)
        with col1:
            make = st.selectbox('Make', make_list, on_change=update_model_fields, key='make') # created a dropdown for make 

            model_field = st.selectbox('Model', st.session_state.model_list, key='model') # created a dropdown for model 
            # trim = st.text_input('Trim/Variant', value='CX Eco') # todo: not passing in model
            year = st.number_input('Year', min_value=1980, max_value=2025, placeholder='e.g. 2016', value=None) # todo: max min year
            mileage = st.number_input('Mileage (km)', min_value=0, max_value=10000000, value=None, placeholder='e.g. 50000')
        with col2:
            transmission = st.selectbox('Transmission', ['Any', 'Automatic', 'Manual', 'Hybrid'])
            engine_capacity = st.number_input('Engine Capacity (cc)', min_value=0, max_value=100000, value=None, placeholder='e.g. 1500')
            fuel_type = st.selectbox('Fuel Type', ['Any', 'Petrol', 'Diesel', 'Electric', 'CNG', 'Hybrid'])
            city = st.selectbox('City', city_list) # created a dropdown for city
            # engine_type = st.text_input('Engine Type/Size', placeholder='e.g. 1.3 VVTi')

        submit = st.button("Estimate Price", use_container_width=True)

    if submit: 
        with st.spinner('Estimating price...'):
            submit_fn(make,model_field,year,mileage,fuel_type,engine_capacity,transmission,city)

    st.write('---')
    st.write('-> Created by [mafgit](https://github.com/mafgit) & [fasihfast](https://github.com/fasihfast)')
    st.write('-> Made using machine learning')
    st.write('-> Data source: [PakWheels](https://www.pakwheels.com/)')

# todo: CI/CD
# todo: feature engineering
# todo: gradient booster