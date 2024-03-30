import streamlit as st
import requests
import json

st.title('Классификация товаров по описанию')

st.subheader('Авторизация')

if 'access_token' not in st.session_state:
    st.session_state.access_token = None

if 'current_form' not in st.session_state:
    st.session_state.current_form = 'login'

if st.session_state.current_form == 'login':
    st.write('Войти в систему:')
    with st.form('login_form'):
        username = st.text_input('Имя пользователя')
        password = st.text_input('Пароль', type='password')
        login_button = st.form_submit_button('Войти')

        if login_button:
            login_data = {
                "username": username,
                "password": password
            }
            login_response = requests.post(url="http://127.0.0.1:8000/token", data=login_data)
            if login_response.status_code == 200:
                st.session_state.access_token = login_response.json().get('access_token')
                st.write('Вход прошел успешно!')
            else:
                st.error('Неправильный логин/пароль')
elif st.session_state.current_form == 'register':
    st.write('Создать новый аккаунт:')
    with st.form('user_create_form'):
        username = st.text_input('Имя пользователя')
        email = st.text_input('Email')
        password = st.text_input('Пароль', type='password')
        user_create_button = st.form_submit_button('Зарегистрироваться')

        if user_create_button:
            user_create_data = {
                'username': username,
                'email': email,
                'password': password
            }
            user_create_response = requests.post(url="http://127.0.0.1:8000/users/", json=user_create_data)
            if user_create_response.status_code == 200:
                st.write('Аккаунт создан!')
                st.session_state.current_form = 'login'
            else:
                st.error('Такой e-mail уже зарегистрирован')

if st.session_state.current_form == 'login':
    if st.button('Зарегистрироваться'):
        st.session_state.current_form = 'register'
else:
    if st.button('Войти'):
        st.session_state.current_form = 'login'

st.subheader('Классификация товаров')

model_type_name = st.radio(label = 'Выберите модель:',
                           options = ['Логистическая регрессия (5 кредиов)', 'Дерево решений (5 кредитов)',
                                      'Случайный лес (10 кредитов)'],
                           horizontal=False)
model_type_names = {
    'Логистическая регрессия (5 кредиов)': 'logreg',
    'Дерево решений (5 кредитов)': 'ds_tree',
    'Случайный лес (10 кредитов)': 'rd_forest'
}
model_type = model_type_names[model_type_name]

input_text = st.text_input('Введите описание товара:')
predict_button = st.button('Определить класс', key='predict_button')
if predict_button:
    if not input_text:
        st.error('Перед определением класса необходимо ввести текст')
    else:
        data = {input_text: 'text'}
        json_data = json.dumps(data)
        params = {'requested_model_type': model_type}
        headers = {'Authorization': f'Bearer {st.session_state.access_token}'}
        predict_response = requests.post(url="http://127.0.0.1:8000/predict", data=json_data, params=params, headers=headers)
        if predict_response.status_code == 200:
            st.write('Ваш текст принадлежит к следующему классу:')
            pred_result = predict_response.json().get('pred_result')
            st.write((pred_result[0]))
        else:
            st.error(f'Error: {predict_response.json().get("detail")}')
