#!/usr/bin/env python
from flask import Flask, render_template, Response, session, request

from camera import Camera
from random import randint
from flask_socketio import SocketIO, emit, disconnect

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        glubnum=randint(1,7)
        glubs='Glub '*glubnum
        socketio.sleep(15)
        count += 1
        socketio.emit('my_response',
                      {'data': glubs, 'count': count},
                      namespace='')    


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('my_event', namespace='')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

@socketio.on('connect', namespace='')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    return Response(Camera().get_frame(),mimetype='image/jpeg')

@app.route('/still')
def still(): 
    return render_template('still.html')




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
