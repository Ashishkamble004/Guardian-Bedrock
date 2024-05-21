import streamlit as st
import boto3
import json
import time


region = boto3.Session().region_name
session = boto3.Session(region_name=region)
lambda_client = session.client('lambda')

st.title("Sentinel")
st.subheader("Your GenAI powered Assistant")
sessionId = ""
# sessionId = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
print(sessionId)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session id
if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = sessionId

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#def simulate_typing(full_response):
#    message_placeholder = st.empty()
#    for chunk in full_response.split():
#        full_response += chunk + " "
#        time.sleep(0.05)
#        # Add a blinking cursor to simulate typing
#        message_placeholder.markdown(full_response + "▌")
#    message_placeholder.markdown(full_response)


#def format_response(answer):
#    """Formats the assistant's response based on content type.

#    Args:
#        answer (str): The assistant's response.
#
#    Returns:
#        str: The formatted response.
#    """

#    if answer.startswith("http"):  # URL
#        return f"[Link]({answer})"
#    elif answer.startswith("```"):  # Code block
#        return st.code(answer)
#    elif "\n" in answer:  # Multi-line text
#        return st.markdown(answer)
#    else:  # Default formatting (markdown)
#        return answer  # No bullet points added here
#
# React to user input
if prompt := st.chat_input("How Can I help?"):

    # Display user input in chat message container
    question = prompt
    st.chat_message("user").markdown(question)

    # Call lambda function to get response from the model
    payload = json.dumps({"question": prompt, "sessionId": st.session_state['sessionId']})
    print(payload)
    result = lambda_client.invoke(
        FunctionName='InvokeKnowledgeBase',
        Payload=payload
    )

    result = json.loads(result['Payload'].read().decode("utf-8"))
    print(result)

    answer = result['body']['answer']
    sessionId = result['body']['sessionId']

    st.session_state['sessionId'] = sessionId

    # Add user input to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
         st.markdown(answer)  # Use the typing simulation with formatted response

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})
