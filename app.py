from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import requests
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# 创建数据库
with app.app_context():
    db.create_all()
    # 创建默认管理员用户
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", is_admin=True)
        db.session.add(admin)
        db.session.commit()

# 直播服务器配置
# 请确保这些地址是正确的，可能需要修改为您实际的服务器地址
LIVE_SERVER = "http://livego:8090"  # 修改为您的实际服务器地址
RTMP_SERVER = "rtmp://192.168.1.200:1935"  # 修改为您的实际RTMP服务器地址
FLV_URL = "http://192.168.1.200:7001/live/movie.flv"  # 修改为您的实际FLV流地址
HLS_URL = "http://192.168.1.200:7002/live/movie.m3u8"  # 修改为您的实际HLS流地址

# 解决跨域问题
@app.route("/flv/<path:filename>")
def proxy_flv(filename):
    try:
        proxy_url = f"http://livego:7001/flv/{filename}"
        r = requests.get(proxy_url, stream=True)

        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk

        return Response(generate(), content_type=r.headers["Content-Type"])
    except Exception as e:
        return str(e), 502


@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("live"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            return redirect(url_for("live"))
        else:
            return render_template("login.html", error="用户名或密码错误")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("is_admin", None)
    return redirect(url_for("login"))


@app.route("/live")
def live():
    if "username" not in session:
        return redirect(url_for("login"))

    # 获取channelkey
    rtmp_push_url = None
    try:
        response = requests.get(f"{LIVE_SERVER}/control/get?room=movie", timeout=5)
        if response.status_code == 200:
            channelkey = response.json().get("data")
            if channelkey:
                rtmp_push_url = f"{RTMP_SERVER}/live/{channelkey}"
    except requests.exceptions.RequestException as e:
        print(f"获取channelkey失败: {e}")

    return render_template(
        "live.html",
        username=session["username"],
        is_admin=session.get("is_admin", False),
        rtmp_push_url=rtmp_push_url,
        flv_url=FLV_URL,
        hls_url=HLS_URL,
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "username" not in session or not session.get("is_admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return render_template("admin.html", error="用户名已存在")

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return render_template("admin.html", success="用户添加成功")

    users = User.query.all()
    return render_template("admin.html", users=users)


@app.route("/chat/send", methods=["POST"])
def send_chat():
    if "username" not in session:
        return jsonify({"status": "error", "message": "未登录"}), 401

    message = request.form.get("message")
    if not message:
        return jsonify({"status": "error", "message": "消息不能为空"}), 400

    chat = ChatMessage(username=session["username"], message=message)
    db.session.add(chat)
    db.session.commit()

    return jsonify({"status": "success"})


@app.route("/chat/messages")
def get_chat_messages():
    if "username" not in session:
        return jsonify({"status": "error", "message": "未登录"}), 401

    messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(50).all()
    messages_data = [
        {
            "username": msg.username,
            "message": msg.message,
            # 将UTC时间转换为本地时间
            "time": msg.timestamp.replace(tzinfo=timezone.utc)
            .astimezone(tz=None)
            .strftime("%H:%M"),
        }
        for msg in reversed(messages)
    ]

    return jsonify({"status": "success", "messages": messages_data})


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
