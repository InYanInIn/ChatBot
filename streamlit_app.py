import streamlit as st
import requests
import uuid

BACKEND_URL = "http://localhost:8000"

if "page" not in st.session_state:
    st.session_state.page = "login"
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None
if "conv_list" not in st.session_state:
    st.session_state.conv_list = []



def auth_headers():
    if st.session_state.jwt_token:
        return {"Authorization": f"Bearer {st.session_state.jwt_token}"}
    return {}

def navigate_to(page):
    st.session_state.page = page
    if page == "login" or page == "registration":
        st.session_state.jwt_token = None
    st.rerun()

def get_all_conversations():
    try:
        response = requests.get(
            f"{BACKEND_URL}/conversation/list",
            headers=auth_headers()
        )
        response.raise_for_status()
        return response.json()  # Список id
    except requests.RequestException as e:
        st.error(f"Failed to fetch conversation list: {e}")
        return []

if st.session_state.page == "login":
    st.title("Login - Chat Application")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            if response.ok:
                st.session_state.jwt_token = response.json()["access_token"]
                navigate_to("chat")
            else:

                st.error("Login failed: Invalid credentials")
                st.write(response.json())
        except requests.RequestException as e:
            st.error(f"Login failed: {e}")

    st.markdown("---")
    if st.button("Go to Registration Page"):
        navigate_to("registration")

elif st.session_state.page == "registration":
    st.title("Registration - Chat Application")

    new_username = st.text_input("New Username(minimum: 3)", key="register_username")
    new_password = st.text_input("New Password(minimum: 8)", type="password", key="register_password")

    if st.button("Register"):
        resp = requests.post(
            f"{BACKEND_URL}/auth/register",
            json={"username": new_username,
                  "password": new_password}
        )
        if resp.ok:
            st.success("Registered! Please login below.")
        else:
            st.error("Registration failed")

    st.markdown("---")
    if st.button("Go to Login Page"):
        navigate_to("login")

elif st.session_state.page == "chat":
    st.title("Chat Application")
    # Get all conversations
    conv_list = get_all_conversations()

    names = [c["conversation_name"] for c in conv_list]
    name_to_id = {c["conversation_name"]: c["id"] for c in conv_list}

    if not names:
        new_conv_id = str(uuid.uuid4())
        default_name = "New Chat"
        resp = requests.post(
            f"{BACKEND_URL}/conversation/start",
            params={"conv_id": new_conv_id, "conv_name": default_name},
            headers=auth_headers()
        )
        if resp.ok:
            names = [default_name]
            name_to_id = {default_name: new_conv_id}
        else:
            st.error("Failed to initialize first conversation.")
            st.stop()

    st.sidebar.header("Conversations")

    if "conv_index" not in st.session_state:
        st.session_state.conv_index = 0
        if "conv_name" not in st.session_state:
            st.session_state.conv_name = names[st.session_state.conv_index]

    selected_name = st.sidebar.selectbox(
        "Choose conversation:",
        names,
        index=st.session_state.conv_index,
    )

    if st.sidebar.button("➕ New conversation"):
        new_conv_id = str(uuid.uuid4())
        default_name = "New Chat " + str(len(names))
        resp = requests.post(
            f"{BACKEND_URL}/conversation/start",
            params={"conv_id": new_conv_id, "conv_name": default_name},
            headers=auth_headers()
        )
        if resp.status_code == 200:

            name_to_id[default_name] = new_conv_id
            names.append(default_name)
            st.session_state.conv_index = names.index(default_name)
            st.session_state.conv_name = default_name
            st.rerun()
        else:
            st.error("Failed to start a new conversation.")
            st.stop()

    selected_conv_id = name_to_id[selected_name]

    if st.sidebar.button("Logout"):
        st.session_state.jwt_token = None
        navigate_to("login")


    # Initialize conversation ID
    if "conv_id" not in st.session_state or st.session_state.conv_id != selected_conv_id:
        st.session_state.conv_id = selected_conv_id

    try:
        response = requests.get(
            f"{BACKEND_URL}/conversation/{st.session_state.conv_id}",
            headers=auth_headers()
        )
        response.raise_for_status()
        st.session_state.messages = response.json()["messages"]
    except requests.RequestException as e:
        st.error(f"Failed to fetch conversation history: {e}")
        st.stop()



    # Display chat messages from history
    for message in st.session_state.messages:
        role = "assistant" if message["role"] == "model" else message["role"]
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("What is up?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Send message to backend and get response
        with st.chat_message("assistant"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/conversation/{st.session_state.conv_id}/message",
                    json={"prompt": prompt, "model": "llama3.2"},
                    headers=auth_headers()
                )
                response.raise_for_status()
                reply = response.json()["generated_text"]

                # Add assistant reply
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.markdown(reply)

                # Set new conversation name if it's the first message
                if len(st.session_state.messages) <= 2:
                    new_conv_name = requests.post(
                        f"{BACKEND_URL}/generation/generate_chat_name",
                        json={"prompt": prompt, "model": "llama3.2"},
                        headers=auth_headers()
                    ).json()["generated_text"][1:-1]
                    resp = requests.post(
                        f"{BACKEND_URL}/conversation/{st.session_state.conv_id}/rename",
                        params={"conv_id": st.session_state.conv_id,
                                "conv_name": new_conv_name},
                        headers=auth_headers()
                    )
                    if resp.status_code == 200:
                        name_to_id[new_conv_name] = st.session_state.conv_id
                        names.append(new_conv_name)
                        st.session_state.conv_index = names.index(new_conv_name)

                        names.remove(st.session_state.conv_name)
                        name_to_id.pop(st.session_state.conv_name)

                        st.session_state.conv_index = names.index(new_conv_name)
                        st.session_state.conv_name = new_conv_name

                        st.rerun()
                    else:
                        st.error("Failed to generate new chat name.")
                        st.stop()
            except requests.RequestException as e:
                st.error(f"Error communicating with the backend: {e}")