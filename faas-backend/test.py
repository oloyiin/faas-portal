def main(context):
    return {
        "message": "Hello from FaaS!",
        "status": "success",
        "function_name": "test-function",
        "context": str(context)
    }
