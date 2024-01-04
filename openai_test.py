# import openai

# # Replace 'your-api-key' with your OpenAI API key
# openai.api_key = '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'

# def test_openai_connection():
#     try:
#         # Attempt to make a test request to the OpenAI API
#         response = openai.Completion.create(
#             engine="text-davinci-003",
#             prompt="Test connection to OpenAI API"
#         )
        
#         # If the request is successful, print the response
#         print("Connection to OpenAI API successful!")
#         print("API Response:")
#         print(response)
#     except Exception as e:
#         # If there's an error, print the error message
#         print("Error connecting to OpenAI API:", str(e))

# if __name__ == "__main__":
#     test_openai_connection()


from openai import OpenAI