import random
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

# Training dataset
training_data = {
    "greeting": ["hi", "hello", "hey", "good morning", "good evening"],
    "goodbye": ["bye", "see you", "goodbye", "take care"],
    "thanks": ["thanks", "thank you", "thx", "cheers"],
    "feelings": ["how are you", "how are you doing", "what's up", "how’s it going"],
    "help": ["can you help me", "i need help", "assist me", "what can you do"],
}

# Responses
responses = {
    "greeting": ["Hello! How can I help you today?", "Hi there!", "Hey! What’s up?"],
    "goodbye": ["Goodbye! Have a nice day!", "See you later!", "Take care!"],
    "thanks": ["You're welcome!", "No problem!", "Anytime!"],
    "feelings": ["I'm just a bot, but I'm doing great!", "Feeling awesome, thanks!"],
    "help": ["I can chat with you and answer simple questions.", "I'm here to help you with small talk!"],
    "default": ["I'm not sure I understand.", "Could you say that another way?", "Interesting... tell me more."]
}

# Prepare training
X_text, y = [], []
for intent, examples in training_data.items():
    for example in examples:
        X_text.append(example)
        y.append(intent)

vectorizer = CountVectorizer()
X = vectorizer.fit_transform(X_text)

clf = LogisticRegression()
clf.fit(X, y)

# Conversation memory
conversation_history = []

def predict_intent(user_input):
    X_test = vectorizer.transform([user_input])
    intent = clf.predict(X_test)[0]
    return intent

def chatbot_response(user_input):
    conversation_history.append({"user": user_input})

    if any(word in user_input for word in ["bye", "exit", "quit"]):
        bot_message = random.choice(responses["goodbye"])
    else:
        intent = predict_intent(user_input)
        bot_message = random.choice(responses.get(intent, responses["default"]))

    conversation_history.append({"bot": bot_message})
    return bot_message, conversation_history
