from flask import Flask, Response, request
import threading
import queue
from langchain.llms import OpenAI
from langchain.callbacks.base import BaseCallbackHandler

app = Flask(__name__)

def chat_thread(prompt, callback_fn):
    chat = OpenAI(
        verbose=True,
        streaming=True,
        callbacks=[callback_fn,],
        temperature=0.7,
        openai_api_key="YOUR-API-KEY"
    )
    chat(prompt)

class StreamCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue: queue.Queue):
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.queue.put(token)

@app.route('/chat', methods=['POST'])
def chain():
    print(request.get_json())
    prompt = request.get_json().get("prompt")
    chat_queue = queue.Queue()
    callback_fn = StreamCallbackHandler(chat_queue)
    thread = threading.Thread(target=chat_thread, args=(prompt, callback_fn))
    thread.start()
    def generate(rq: queue.Queue):
        while thread.is_alive() or not rq.empty():
            yield "data:"+rq.get()+'\n\n\n'
    return Response(generate(chat_queue), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(threaded=True, debug=True)