from django.shortcuts import render

def chat(request):
    if request.method == "POST":
        user_message = request.POST.get("message", "")
        bot_response = "Sorry, I don’t understand."
        
        if "price" in user_message.lower():
            bot_response = "You can check our prices in the catalog."
        elif "hello" in user_message.lower():
            bot_response = "Hello! How can I help you?"

        # Return the response in a rendered HTML template
        return render(request, 'chatbot/chat.html', {'user_message': user_message, 'bot_response': bot_response})

    return render(request, 'chatbot/chat.html')
