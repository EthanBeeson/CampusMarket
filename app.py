import streamlit as st

st.write("hello world")
x = st.text_input("Favorite Movie?")

st.write(f"your favorite movie is: {x} !")

is_clicked = st.button("Click me")