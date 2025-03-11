import os
import json
# import dialogflow_v2 as dialogflow
from google.cloud import dialogflow_v2 as dialogflow
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import ChatMessage
from django.shortcuts import render
from products.models import Product
from dotenv import load_dotenv


load_dotenv()

# Get Dialogflow Project ID from environment variable
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")

def get_dialogflow_response(text, session_id):
    """Send user input to Dialogflow and return bot response."""
    try:
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)  # FIXED

        text_input = dialogflow.TextInput(text=text, language_code="en")
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(session=session, query_input=query_input)

        return response.query_result.fulfillment_text

    except Exception as e:
        print("Dialogflow Error:", str(e))  # Print error for debugging
        return "Sorry, I couldn't process your request at the moment. Please try again later."



@csrf_exempt
@login_required
def chatbot_view(request):
    """Handle user messages and return chatbot responses."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            user = request.user

            if not user_message:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)

            # Get bot response from Dialogflow
            bot_response = get_dialogflow_response(user_message, session_id=str(user.id))

            # Save user message
            ChatMessage.objects.create(user=user, message=user_message, role="user")

            # Save bot response
            ChatMessage.objects.create(user=user, message=bot_response, role="bot")

            return JsonResponse({"response": bot_response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    # If the request method is GET, render the chatbot HTML page
    return render(request, "chatbot/chat.html", {"chats": ChatMessage.objects.filter(user=request.user)})




# @csrf_exempt
# def dialogflow_webhook(request):
#     """Handles Dialogflow webhook requests."""
#     try:
#         data = json.loads(request.body)
#         intent_name = data["queryResult"]["intent"]["displayName"]

#         if intent_name == "product_inquiry":
#             response_text = get_product_list()  # Fetch from DB
#         else:
#             response_text = "I'm not sure how to help with that."

#         return JsonResponse({"fulfillmentText": response_text})

#     except Exception as e:
#         return JsonResponse({"fulfillmentText": "Sorry, an error occurred."})

# def get_product_list():
#     """Fetches product categories from the database."""
#     products = Product.objects.values_list("category", flat=True).distinct()
#     product_list = ", ".join(products)
#     return f"We offer the following products: {product_list}."

